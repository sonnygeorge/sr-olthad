from typing import Callable, List, Optional

from pydantic import BaseModel

from agent_framework.schema import Agent, InstructLmMessage, LmStreamHandler
from sr_olthad.olthad import TaskNode


class PlannerInputData(BaseModel):
    env_state: str
    olthad: TaskNode  # I.e., the root task node w/ all the descendants


class PlannerOutputData(BaseModel):
    new_plan: List[TaskNode]  # TODO: Optional for no plan change?


class PlannerReturn:
    output_data: PlannerOutputData


class Planner(Agent):
    def __init__(
        self,
        stream_handler: Optional[LmStreamHandler] = None,
        callback_after_each_lm_step: Optional[
            Callable[[List[InstructLmMessage]], None]
        ] = None,
    ):
        self.stream_handler = stream_handler
        self.callback_after_each_lm_step = callback_after_each_lm_step

    async def __call__(self, input_data: PlannerInputData) -> PlannerReturn:
        # TODO: Raise error if `new_plan` is empty
        pass  # TODO
