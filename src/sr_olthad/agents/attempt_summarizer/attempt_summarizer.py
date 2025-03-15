from typing import List

from pydantic import BaseModel

from sr_olthad.olthad import AttemptedTaskStatus
from agent_framework.schema import Agent, InstructLmMessage


class AttemptSummarizerInputData(BaseModel):
    env_state: str


class AttemptSummarizerOutputData(BaseModel):
    chosen_status: AttemptedTaskStatus
    retrospective: str


class AttemptSummarizerSummarizerReturn:
    output_data: AttemptSummarizerOutputData
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class AttemptSummarizer(Agent):
    async def __call__(
        self, input_data: AttemptSummarizerInputData
    ) -> AttemptSummarizerSummarizerReturn:
        pass
