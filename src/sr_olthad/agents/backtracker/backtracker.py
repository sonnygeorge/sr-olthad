from jinja2 import Template
from pydantic import BaseModel


from schema import Agent, AgentReturn
from single_turn_chat_agent import SingleTurnChatMultipleChoiceAgent
import sr_olthad.config as cfg
from sr_olthad.enums import BacktrackedFromTaskStatus
from sr_olthad.olthad import OlthadTraversal, TaskNode


class BacktrackerInputData(BaseModel):
    env_state: str
    olthad: TaskNode  # I.e., the root task node w/ all the descendants


class BacktrackerOutputData(BaseModel):
    chosen_status: BacktrackedFromTaskStatus
    retrospective: str


class BacktrackerReturn(AgentReturn):
    output_data: BacktrackerOutputData


MULTIPLE_CHOICE_OPTIONS = ["A", "B"]


class Backtracker(Agent):
    def __init__(self):
        # Initialize exhaustive effort classifier
        self.exhaustive_effort_clf: SingleTurnChatMultipleChoiceAgent[
            BacktrackerInputData
        ] = SingleTurnChatMultipleChoiceAgent(
            instruct_lm=cfg.AgentInstructLms.EXHAUSTIVE_EFFORT_CLF,
            multiple_choice_options=MULTIPLE_CHOICE_OPTIONS,
            sys_prompt=cfg.AgentPrompts.EXHAUSTIVE_EFFORT_CLF.sys_prompt,
            user_prompt_template=cfg.AgentPrompts.EXHAUSTIVE_EFFORT_CLF.user_prompt,
            input_data_model=BacktrackerInputData,
        )

    async def __call__(self, input_data: BacktrackerInputData) -> BacktrackerReturn:
        pass  # TODO
