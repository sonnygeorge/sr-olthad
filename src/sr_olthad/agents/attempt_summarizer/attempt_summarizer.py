import inspect
from typing import Optional

from loguru import logger

from agent_framework.agents import SingleTurnChatAgent
from agent_framework.schema import LmStreamsHandler
from agent_framework.utils import prepare_input_messages
from sr_olthad.agents.attempt_summarizer.prompt import (
    PROMPT_REGISTRY,
    AttemptSummarizerLmResponseOutputData,
    AttemptSummarizerPromptInputData,
)
from sr_olthad.config import AttemptSummarizerCfg as cfg
from sr_olthad.emissions import (
    PostLmGenerationStepEmission,
    PostLmGenerationStepHandler,
    PreLmGenerationStepEmission,
    PreLmGenerationStepHandler,
)
from sr_olthad.olthad import OlthadTraversal
from sr_olthad.schema import AgentName


class AttemptSummarizer:
    def __init__(
        self,
        olthad_traversal: OlthadTraversal,
        pre_lm_generation_step_handler: Optional[
            PreLmGenerationStepHandler
        ] = None,
        post_lm_generation_step_handler: Optional[
            PostLmGenerationStepHandler
        ] = None,
        streams_handler: Optional[LmStreamsHandler] = None,
    ):
        self.traversal = olthad_traversal
        self.streams_handler = streams_handler
        self.pre_lm_generation_step_handler = pre_lm_generation_step_handler
        self.post_lm_step_handler = post_lm_generation_step_handler

        attempt_summarizer_prompts = PROMPT_REGISTRY[cfg.PROMPTS_VERSION]
        self._attempt_summarizer: SingleTurnChatAgent[
            AttemptSummarizerLmResponseOutputData
        ] = SingleTurnChatAgent(
            instruct_lm=cfg.INSTRUCT_LM,
            response_json_data_model=AttemptSummarizerLmResponseOutputData,
            # TODO: Render sys prompt dynamically, e.g., w/ RAG of relevant good examples
            sys_prompt=attempt_summarizer_prompts.sys_prompt_template.render(),
            user_prompt_template=attempt_summarizer_prompts.user_prompt_template,
            max_tries_to_get_valid_response=cfg.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
            logger=logger,
        )

    async def __call__(self, env_state: str) -> None:
        # Prepare input data
        attempted_subtask = self.traversal.cur_node.in_progress_subtask
        input_data = AttemptSummarizerPromptInputData(
            env_state=env_state,
            olthad=self.traversal.root_node.stringify(
                obfuscate_status_of=attempted_subtask.id
            ),
            attempted_subtask_node=attempted_subtask.stringify(
                obfuscate_status_of=attempted_subtask.id
            ),
        )

        # Pre-LM-generation step handler
        if self.pre_lm_generation_step_handler is not None:
            in_messages = prepare_input_messages(
                input_data,
                user_prompt_template=...,
                sys_prompt=...,
            )
            emission = PreLmGenerationStepEmission(
                agent_name=AgentName.ATTEMPT_SUMMARIZER,
                prompt_messages=in_messages,
                n_streams_to_handle=1,
            )
            if inspect.iscoroutinefunction(
                self.pre_lm_generation_step_handler
            ):
                await self.pre_lm_generation_step_handler(emission)
            else:
                self.pre_lm_generation_step_handler(emission)

        step_is_approved = False
        while not step_is_approved:
            # Invoke `self._attempt_summarizer`
            return_obj = await self._attempt_summarizer(
                prompt_template_data=input_data,
                stream_handler=self.streams_handler,
            )

            if self.post_lm_step_handler is None:
                break
            # Otherwise, call the post-LM-generation step handler to get approval
            make_update_after_approval = self.traversal.cur_node.update_status_and_retrospective_of_in_progress_subtask(
                return_obj.output_data.status_to_assign,
                return_obj.output_data.retrospective_to_assign,
                should_yield_diff_and_receive_approval_before_update=True,
                diff_root_node=self.traversal.root_node,
            )
            difflines = next(make_update_after_approval)
            full_messages = return_obj.messages
            emission = PostLmGenerationStepEmission(
                diff_lines=difflines,
                full_messages=full_messages,
            )
            if inspect.iscoroutinefunction(self.post_lm_step_handler):
                step_is_approved = await self.post_lm_step_handler(emission)
            else:
                step_is_approved = self.post_lm_step_handler(emission)

            # Send approval back to generator so it knows to make update
            make_update_after_approval.send(step_is_approved)
