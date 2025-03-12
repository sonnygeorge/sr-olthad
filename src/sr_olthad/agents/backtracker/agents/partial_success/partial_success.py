from typing import List

from pydantic import BaseModel

from schema import InstructLmAgentReturn, InstructLmMessage


class PartialSuccessClfInputData(BaseModel):
    pass  # TODO


class PartialSuccessClfOutputData(BaseModel):
    pass  # TODO


class PartialSuccessClfReturn(InstructLmAgentReturn):
    output_data: PartialSuccessClfOutputData
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class PartialSuccessClf(InstructLmAgentReturn):
    async def __call__(self, input_data: PartialSuccessClfInputData) -> PartialSuccessClfReturn:
        pass  # TODO
