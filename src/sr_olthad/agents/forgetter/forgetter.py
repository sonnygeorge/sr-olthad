from typing import List

from pydantic import BaseModel

from agent_framework.schema import Agent, InstructLmMessages


class ForgetterInputData(BaseModel):
    pass  # TODO


class ForgetterOutputData(BaseModel):
    pass  # TODO


class ForgetterReturn:
    output_data: ForgetterOutputData
    messages: InstructLmMessages | List[InstructLmMessages]


class Forgetter(Agent):
    async def __call__(
        self, input_data: ForgetterInputData
    ) -> ForgetterReturn:
        pass  # TODO
