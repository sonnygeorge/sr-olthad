import inspect
from typing import Optional

from loguru import logger

from agent_framework.agents import InstructLmChatAgent
from agent_framework.schema import LmStreamsHandler
from agent_framework.utils import render_single_turn_prompt_templates_and_get_messages
from sr_olthad.agents.attempt_summarizer.prompt import (
    PROMPT_REGISTRY,
    AttemptSummarizerLmResponseOutputData,
    AttemptSummarizerPromptInputData,
)
from sr_olthad.config import AttemptSummarizerCfg as cfg
from sr_olthad.emissions import (
    PostLmGenerationStepEmission,
    PostLmGenerationStepHandlerAndApprover,
    PreLmGenerationStepEmission,
    PreLmGenerationStepHandler,
)
from sr_olthad.olthad import OlthadTraversal
from sr_olthad.schema import AgentName


class AttemptSummarizer:
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
        self.post_lm_step_handler = post_lm_generation_step_handler

        self._attempt_summarizer: InstructLmChatAgent[
            AttemptSummarizerLmResponseOutputData
        ] = InstructLmChatAgent(
            instruct_lm=cfg.INSTRUCT_LM,
            response_json_data_model=AttemptSummarizerLmResponseOutputData,
            max_tries_to_get_valid_response=cfg.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
            logger=logger,
        )

    async def __call__(self, env_state: str) -> None:
        raise NotImplementedError
