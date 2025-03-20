from typing import Optional

from agent_framework.schema import Agent, LmStreamsHandler
from sr_olthad.emissions import (
    PostLmGenerationStepHandlerAndApprover,
    PreLmGenerationStepHandler,
)
from sr_olthad.olthad import OlthadTraversal


class Forgetter(Agent):
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

    async def __call__(self, env_state: str) -> None:
        raise NotImplementedError
