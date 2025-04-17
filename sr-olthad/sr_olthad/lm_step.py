from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel

from sr_olthad.framework.agents import (
    InstructLmAgentOutput,
    InstructLmAgentRunMethod,
    LmRetryHandler,
)
from sr_olthad.framework.schema import InstructLmMessage
from sr_olthad.olthad import PendingOlthadUpdate
from sr_olthad.schema import (
    GetDomainSpecificSysPromptInputData,
    LmAgentName,
    UserPromptInputData,
)
from sr_olthad.utils import get_input_messages


class PreLmStepEmission(BaseModel):
    lm_agent_name: LmAgentName
    cur_node_id: str
    input_messages: list[InstructLmMessage]
    n_streams_to_handle: int = 1


class PostLmStepEmission(BaseModel):
    diff: list[str]
    full_messages: list[InstructLmMessage] | list[list[InstructLmMessage]]


class PreLmStepHandler(Protocol):
    """
    Callable that handles a `PreLmGenerationStepEmission`.

    Args:
        emission (PreLmGenerationStepEmission): Emission data
    """

    def __call__(self, emission: PreLmStepEmission) -> None: ...


class PostLmStepApprover(Protocol):
    """
    Callable that handles a `PostLmGenerationStepEmission` and returns whether to "approve"
    the LM generation step or force a re-run of the LM generation step.

    Args:
        emission (PostLmGenerationStepEmission): Emission data.
    Returns:
        bool: Whether to accept the step emission or force a re-run.
    """

    def __call__(self, emission: PostLmStepEmission) -> bool: ...


LmStepOutputT = TypeVar("LmStepOutputT")


class LmStep(Protocol, Generic[LmStepOutputT]):
    async def __call__(self) -> LmStepOutputT: ...


@dataclass
class LmStepTemplate:
    pre_lm_step_handler: PreLmStepHandler = lambda _: None
    lm_retry_handler: LmRetryHandler = lambda _, __: None
    post_lm_step_approver: PostLmStepApprover = lambda _: True
    get_domain_specific_sys_prompt_input_data: GetDomainSpecificSysPromptInputData | None = (
        None
    )

    def compose(
        self,
        run_step: InstructLmAgentRunMethod,
        process_output: Callable[
            [InstructLmAgentOutput], tuple[LmStepOutputT, PendingOlthadUpdate]
        ],
        lm_agent_name: LmAgentName,
        cur_node_id: str,
        prompt_input_data: UserPromptInputData,
        n_streams_to_handle: int = 1,
    ) -> LmStep[LmStepOutputT]:
        async def _lm_step() -> LmStepOutputT:
            # Get sys prompt input data dynamically by calling the getter callback if any
            if self.get_domain_specific_sys_prompt_input_data is None:
                sys_prompt_input_data = None
            else:
                sys_prompt_input_data = self.get_domain_specific_sys_prompt_input_data(
                    lm_agent_name=lm_agent_name, user_prompt_input_data=prompt_input_data
                )

            # Get input messages
            input_messages = get_input_messages(
                lm_agent_name=lm_agent_name,
                user_prompt_input_data=prompt_input_data,
                sys_prompt_input_data=sys_prompt_input_data,
            )

            # Prepare pre-lm callback
            pre_step_emission = PreLmStepEmission(
                lm_agent_name=lm_agent_name,
                cur_node_id=cur_node_id,
                input_messages=input_messages,
                n_streams_to_handle=n_streams_to_handle,
            )

            # Run step until approved
            step_is_approved = False
            while not step_is_approved:
                await self.pre_lm_step_handler(pre_step_emission)
                output = await run_step(
                    input_messages=input_messages,
                    retry_callback=self.lm_retry_handler,
                )
                return_if_approved, pending_update = process_output(output)
                post_step_emission = PostLmStepEmission(
                    diff=pending_update.get_diff(),
                    full_messages=output.messages,
                )
                step_is_approved = await self.post_lm_step_approver(post_step_emission)
                if step_is_approved:
                    pending_update.commit()
                    return return_if_approved

        return _lm_step
