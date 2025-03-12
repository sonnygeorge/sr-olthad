from typing import List

from pydantic import BaseModel

from sr_olthad.enums import AttemptedTaskStatus
from schema import InstructLmAgentReturn, InstructLmMessage


class AttemptSummarizerInputData(BaseModel):
    env_state: str


class AttemptSummarizerOutputData(BaseModel):
    chosen_status: AttemptedTaskStatus
    retrospective: str


class AttemptSummarizerSummarizerReturn(InstructLmAgentReturn):
    output_data: AttemptSummarizerOutputData
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class AttemptSummarizer(InstructLmAgentReturn):
    async def __call__(
        self, input_data: AttemptSummarizerInputData
    ) -> AttemptSummarizerSummarizerReturn:
        # TODO: Actual inference if it's needed later
        output_data = AttemptSummarizerOutputData(summary=input_data.env_state)
        return AttemptSummarizerSummarizerReturn(output_data=output_data, messages=[])
