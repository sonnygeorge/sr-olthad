from typing import List

from pydantic import BaseModel

from schema import InstructLmAgentReturn, InstructLmMessage


class ExhaustiveEffortClfInputData(BaseModel):
    pass  # TODO


class ExhaustiveEffortClfOutputData(BaseModel):
    pass  # TODO


class ExhaustiveEffortClfReturn(InstructLmAgentReturn):
    output_data: ExhaustiveEffortClfOutputData
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class ExhaustiveEffortClf(InstructLmAgentReturn):
    async def __call__(
        self, input_data: ExhaustiveEffortClfInputData
    ) -> ExhaustiveEffortClfReturn:
        pass  # TODO
