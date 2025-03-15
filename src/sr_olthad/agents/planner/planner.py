from typing import Callable, List, Optional

from loguru import logger
from pydantic import BaseModel

from agent_framework.agents import SingleTurnChatAgent
from agent_framework.schema import Agent, InstructLmMessage, LmStreamHandler
from sr_olthad.agents.planner.prompt import (
    PLANNER_PROMPT_REGISTRY,
    PlannerLmResponseOutputData,
)
from sr_olthad.config import PlannerCfg as cfg
from sr_olthad.olthad import TaskNode


class PlannerInputData(BaseModel):
    """
    Input data for the Planner agent.

    Attributes:
        env_state (str): PRE-STRINGIFIED current environment state.
        root_task_node (TaskNode): The root task node of the OLTHAD.
        current_task_node (TaskNode): The task node we're considering backtracking from.
    """

    env_state: str
    root_task_node: TaskNode
    current_task_node: TaskNode


class PlannerOutputData(BaseModel):
    new_planned_subtasks: List[str]


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

        # exhaustive_effort_prompts = EXHAUSTIVE_EFFORT_CLF_PROMPT_REGISTRY[
        #     cfg.ExhaustiveEffortClf.PROMPTS_VERSION
        # ]
        # self.exhaustive_effort_clf: SingleTurnChatAgent[
        #     BacktrackerSubAgentLmResponseOutputData
        # ] = SingleTurnChatAgent(
        #     instruct_lm=cfg.ExhaustiveEffortClf.INSTRUCT_LM,
        #     response_json_data_model=BacktrackerSubAgentLmResponseOutputData,
        #     # TODO: Render sys prompt dynamically, e.g., w/ RAG of relevant good examples
        #     sys_prompt=exhaustive_effort_prompts.sys_prompt_template.render(),
        #     user_prompt_template=exhaustive_effort_prompts.user_prompt_template,
        #     max_tries_to_get_valid_response=cfg.ExhaustiveEffortClf.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
        # )

        planner_prompts = PLANNER_PROMPT_REGISTRY[cfg.PROMPTS_VERSION]
        self._planner: SingleTurnChatAgent[PlannerLmResponseOutputData] = (
            SingleTurnChatAgent(
                instruct_lm=cfg.INSTRUCT_LM,
                response_json_data_model=PlannerLmResponseOutputData,
                # TODO: Render sys prompt dynamically, e.g., w/ RAG of relevant good examples
                sys_prompt=planner_prompts.sys_prompt_template.render(),
                user_prompt_template=planner_prompts.user_prompt_template,
                max_tries_to_get_valid_response=cfg.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
                logger=logger,
            )
        )

    async def __call__(self, input_data: PlannerInputData) -> PlannerReturn:
        # TODO: Raise error if `new_plan` is empty
        pass  # TODO
