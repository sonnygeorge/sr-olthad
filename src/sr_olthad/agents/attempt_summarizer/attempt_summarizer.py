from typing import Callable, List, Optional

from loguru import logger
from pydantic import BaseModel

from agent_framework.agents import SingleTurnChatAgent
from agent_framework.schema import Agent, InstructLmMessage, LmStreamHandler
from sr_olthad.agents.attempt_summarizer.prompt import (
    PROMPT_REGISTRY,
    AttemptSummarizerLmResponseOutputData,
    AttemptSummarizerPromptInputData,
)
from sr_olthad.config import AttemptSummarizerCfg as cfg
from sr_olthad.task_node import AttemptedTaskStatus, TaskNode


class AttemptSummarizerInputData(BaseModel):
    """
    Input data for the Attempt Summarizer agent.

    Attributes:
        env_state (str): PRE-STRINGIFIED current environment state.
        root_task_node (TaskNode): The root task node of the OLTHAD.
        attempted_subtask_node (TaskNode): The subtask node whose attempt we want to
            summarize.
    """

    env_state: str
    root_task_node: TaskNode
    attempted_subtask_node: TaskNode


class AttemptSummarizerOutputData(BaseModel):
    status_to_assign: AttemptedTaskStatus
    retrospective_to_assign: str


class AttemptSummarizerSummarizerReturn(BaseModel):
    output_data: AttemptSummarizerOutputData


class AttemptSummarizer(Agent):
    def __init__(
        self,
        stream_handler: Optional[LmStreamHandler] = None,
        callback_after_each_lm_step: Optional[
            Callable[[List[InstructLmMessage]], None]
        ] = None,
    ):
        self.stream_handler = stream_handler
        self.callback_after_each_lm_step = callback_after_each_lm_step

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

    async def __call__(
        self, input_data: AttemptSummarizerInputData
    ) -> AttemptSummarizerSummarizerReturn:
        planner_input_data = AttemptSummarizerPromptInputData(
            env_state=input_data.env_state,
            olthad=input_data.root_task_node.stringify(
                obfuscate_status_of=input_data.attempted_subtask_node.id
            ),
            attempted_subtask_node=input_data.attempted_subtask_node.stringify(
                obfuscate_status_of=input_data.attempted_subtask_node.id
            ),
        )
        return_obj = await self._attempt_summarizer(
            prompt_template_data=planner_input_data,
            stream_handler=self.stream_handler,
        )
        if self.callback_after_each_lm_step is not None:
            self.callback_after_each_lm_step(return_obj.messages)

        status_to_assign_str = return_obj.output_data.status_to_assign
        status_to_assign = None
        for status in AttemptedTaskStatus:
            clean_status = status.value.lower().strip()
            clean_status_to_assign_str = status_to_assign_str.lower().strip()
            if clean_status == clean_status_to_assign_str:
                status_to_assign = status
                break
        if status_to_assign is None:
            raise NotImplementedError(
                f"LM-assigned '{status_to_assign_str}' is not recognized. "
                "Handling this is not yet implemented."
            )

        return AttemptSummarizerSummarizerReturn(
            output_data=AttemptSummarizerOutputData(
                status_to_assign=status_to_assign,
                retrospective_to_assign=return_obj.output_data.retrospective_to_assign,
            )
        )
