from typing import Callable, List, Optional

from pydantic import BaseModel

from agent_framework.schema import Agent, InstructLmMessage, LmStreamHandler
from sr_olthad.olthad import AttemptedTaskStatus, TaskNode


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


class AttemptSummarizerSummarizerReturn:
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

    async def __call__(
        self, input_data: AttemptSummarizerInputData
    ) -> AttemptSummarizerSummarizerReturn:
        pass
