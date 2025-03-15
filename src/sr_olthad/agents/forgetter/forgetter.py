from typing import List

from pydantic import BaseModel

from sr_olthad.olthad import AttemptedTaskStatus
from agent_framework.schema import Agent, InstructLmMessage


class ForgetterInputData(BaseModel):
    pass  # TODO


class ForgetterOutputData(BaseModel):
    pass  # TODO


class ForgetterReturn:
    output_data: ForgetterOutputData
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class Forgetter(Agent):
    async def __call__(self, input_data: ForgetterInputData) -> ForgetterReturn:
        pass  # TODO
