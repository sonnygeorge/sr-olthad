from typing import Optional

from loguru import logger

from agent_framework.agents import InstructLmChatAgent
from agent_framework.schema import Agent, LmStreamsHandler
from sr_olthad.agents.planner.prompt import PlannerLmResponseOutputData
from sr_olthad.config import PlannerCfg as cfg
from sr_olthad.emissions import (
    PostLmGenerationStepHandlerAndApprover,
    PreLmGenerationStepHandler,
)
from sr_olthad.olthad import OlthadTraversal


class Planner(Agent):
    def __init__(
        self,
        olthad_traversal: OlthadTraversal,
        pre_lm_generation_step_handler: Optional[PreLmGenerationStepHandler] = None,
        post_lm_generation_step_handler: Optional[
            PostLmGenerationStepHandlerAndApprover
        ] = None,
        streams_handler: Optional[LmStreamsHandler] = None,
    ):

        self.traversal = olthad_traversal
        self.streams_handler = streams_handler
        self.pre_lm_generation_step_handler = pre_lm_generation_step_handler
        self.post_lm_generation_step_handler = post_lm_generation_step_handler

        self._planner: InstructLmChatAgent[PlannerLmResponseOutputData] = (
            InstructLmChatAgent(
                instruct_lm=cfg.INSTRUCT_LM,
                response_json_data_model=PlannerLmResponseOutputData,
                max_tries_to_get_valid_response=cfg.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
                logger=logger,
            )
        )

    async def __call__(self, env_state) -> None:
        raise NotImplementedError
