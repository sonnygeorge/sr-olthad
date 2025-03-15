from typing import List

from pydantic import BaseModel

from agent_framework.schema import Agent, InstructLmMessages
from sr_olthad.olthad import TaskNode


class PlannerInputData(BaseModel):
    env_state: str
    olthad: TaskNode  # I.e., the root task node w/ all the descendants


class PlannerOutputData(BaseModel):
    new_plan: List[TaskNode]  # TODO: Optional for no plan change?


class PlannerReturn:
    output_data: PlannerOutputData
    messages: InstructLmMessages | List[InstructLmMessages]


class Planner(Agent):
    async def __call__(self, input_data: PlannerInputData) -> PlannerReturn:
        # TODO: Raise error if `new_plan` is empty
        pass  # TODO
