from pydantic import BaseModel

from sr_olthad.enums import BacktrackedFromTaskStatus
from sr_olthad.olthad import OlthadTraversal, TaskNode
from schema import Agent, AgentReturn


class BacktrackerInputData(BaseModel):
    env_state: str
    olthad_traversal: OlthadTraversal


class BacktrackerOutputData(BaseModel):
    chosen_status: BacktrackedFromTaskStatus
    retrospective: str


class BacktrackerReturn(AgentReturn):
    output_data: BacktrackerOutputData


class Backtracker(Agent):
    async def __call__(self, input_data: BacktrackerInputData) -> BacktrackerReturn:
        pass  # TODO
