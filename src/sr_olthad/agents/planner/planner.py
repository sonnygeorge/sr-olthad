from typing import List

from pydantic import BaseModel

from schema import InstructLmAgentReturn, InstructLmMessage
from sr_olthad.olthad.task_node import TaskNode


class PlannerInputData(BaseModel):
    env_state: str
    olthad: TaskNode  # I.e., the root task node w/ all the descendants


class PlannerOutputData(BaseModel):
    new_plan: List[TaskNode]  # TODO: Optional for no plan change?


class PlannerReturn(InstructLmAgentReturn):
    output_data: PlannerOutputData
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class Planner(InstructLmAgentReturn):
    async def __call__(self, input_data: PlannerInputData) -> PlannerReturn:
        # TODO: Raise error if `new_plan` is empty
        pass  # TODO
