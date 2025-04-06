from collections.abc import Callable
from dataclasses import dataclass
from typing import Generic, Protocol, TypeVar

from pydantic import BaseModel

from sr_olthad.common.agents import (
    InstructLmAgentOutput,
    InstructLmAgentRunMethod,
    LmRetryHandler,
)
from sr_olthad.common.schema import InstructLmMessage
from sr_olthad.common.utils import render_single_turn_prompt_templates_and_get_messages
from sr_olthad.olthad import PendingOlthadUpdate
from sr_olthad.registry import LM_AGENT_CONFIGS_REGISTRY, PROMPT_REGISTRIES_REGISTRY
from sr_olthad.schema import CommonSysPromptInputData, CommonUserPromptInputData, LmAgentName


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


class GetDomainSpecificInsert(Protocol):
    """
    Callable that takes an LmAgentName and returns a domain-specific insert for the LM
    agent prompts.

    Args:
        lm_agent_name (LmAgentName): The name of the LM agent.
        input_data (CommonUserPromptInputData): The input data for the current invocation
            of the LM agent.

    Returns:
        str: The domain-specific prompt insert
    """

    def __call__(
        self, lm_agent_name: LmAgentName, input_data: CommonUserPromptInputData
    ) -> str: ...


LmStepOutputT = TypeVar("LmStepOutputT")


class LmStep(Protocol, Generic[LmStepOutputT]):
    async def __call__(self) -> LmStepOutputT: ...


@dataclass
class LmStepTemplate:
    pre_lm_step_handler: PreLmStepHandler = lambda _: None
    lm_retry_handler: LmRetryHandler = lambda _, __: None
    post_lm_step_approver: PostLmStepApprover = lambda _: True
    get_domain_specific_insert: GetDomainSpecificInsert | None = None

    def compose(
        self,
        run_step: InstructLmAgentRunMethod,
        process_output: Callable[
            [InstructLmAgentOutput], tuple[LmStepOutputT, PendingOlthadUpdate]
        ],
        lm_agent_name: LmAgentName,
        cur_node_id: str,
        prompt_input_data: CommonUserPromptInputData,
        n_streams_to_handle: int = 1,
    ) -> LmStep[LmStepOutputT]:
        async def _lm_step() -> LmStepOutputT:
            input_messages = get_input_messages(
                lm_agent_name=lm_agent_name,
                user_prompt_input_data=prompt_input_data,
                get_domain_specific_insert=self.get_domain_specific_insert,
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


def get_input_messages(
    lm_agent_name: LmAgentName,
    user_prompt_input_data: CommonUserPromptInputData,
    get_domain_specific_insert: GetDomainSpecificInsert | None = None,
) -> list[InstructLmMessage]:
    """
    Gets agent prompt templates from the registries and renders necessary data into them.
    """
    cfg = LM_AGENT_CONFIGS_REGISTRY[lm_agent_name]
    prompt_registry = PROMPT_REGISTRIES_REGISTRY[lm_agent_name]

    if get_domain_specific_insert is None:
        sys_prompt_input_data = None
    else:
        sys_prompt_input_data = CommonSysPromptInputData(
            domain_specific_insert=get_domain_specific_insert(
                lm_agent_name, user_prompt_input_data
            ),
        )

    return render_single_turn_prompt_templates_and_get_messages(
        user_prompt_template=prompt_registry[cfg.PROMPTS_VERSION].user_prompt_template,
        user_prompt_input_data=user_prompt_input_data,
        sys_prompt_template=prompt_registry[cfg.PROMPTS_VERSION].sys_prompt_template,
        sys_prompt_input_data=sys_prompt_input_data,
    )
