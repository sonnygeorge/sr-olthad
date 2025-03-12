from typing import List

from pydantic import BaseModel

from schema import InstructLmAgentReturn, InstructLmMessage


class SuccessfulCompletionClfInputData(BaseModel):
    pass  # TODO


class SuccessfulCompletionClfOutputData(BaseModel):
    pass  # TODO


class SuccessfulCompletionClfReturn(InstructLmAgentReturn):
    output_data: SuccessfulCompletionClfOutputData
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class SuccessfulCompletionClf(InstructLmAgentReturn):
    async def __call__(
        self, input_data: SuccessfulCompletionClfInputData
    ) -> SuccessfulCompletionClfReturn:
        pass  # TODO
