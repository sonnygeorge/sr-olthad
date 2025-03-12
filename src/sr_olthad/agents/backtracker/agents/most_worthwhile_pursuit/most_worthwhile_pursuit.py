from typing import List

from pydantic import BaseModel

from schema import InstructLmAgentReturn, InstructLmMessage


class MostWorthwhilePursuitClfInputData(BaseModel):
    pass  # TODO


class MostWorthwhilePursuitClfOutputData(BaseModel):
    pass  # TODO


class MostWorthwhilePursuitClfReturn(InstructLmAgentReturn):
    output_data: MostWorthwhilePursuitClfOutputData
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class MostWorthwhilePursuitClf(InstructLmAgentReturn):
    async def __call__(
        self, input_data: MostWorthwhilePursuitClfInputData
    ) -> MostWorthwhilePursuitClfReturn:
        pass  # TODO
