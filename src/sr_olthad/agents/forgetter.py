from typing import List

from pydantic import BaseModel

from schema import InstructLmAgentReturn, InstructLmMessage


class ForgetterInputData(BaseModel):
    pass  # TODO


class ForgetterOutputData(BaseModel):
    pass  # TODO


class ForgetterReturn(InstructLmAgentReturn):
    output_data: ForgetterOutputData
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class Forgetter(InstructLmAgentReturn):
    async def __call__(self, input_data: ForgetterInputData) -> ForgetterReturn:
        pass  # TODO
