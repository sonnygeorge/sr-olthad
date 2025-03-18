from typing import Callable, List, Optional

from pydantic import BaseModel

from agent_framework.schema import Agent, InstructLmMessage, LmStreamHandler


class ForgetterInputData(BaseModel):
    pass  # TODO


class ForgetterOutputData(BaseModel):
    pass  # TODO


class ForgetterReturn:
    output_data: ForgetterOutputData


class Forgetter(Agent):
    def __init__(
        self,
        stream_handler: Optional[LmStreamHandler] = None,
        callback_after_lm_generation_steps: Optional[
            Callable[[List[InstructLmMessage]], None]
        ] = None,
    ):
        self.stream_handler = stream_handler
        self.callback_after_each_lm_step = callback_after_lm_generation_steps

    async def __call__(
        self, input_data: ForgetterInputData
    ) -> ForgetterReturn:
        pass  # TODO
