from typing import Callable, List, Optional

from loguru import logger
from pydantic import BaseModel

from agent_framework.agents import SingleTurnChatAgent
from agent_framework.schema import Agent, InstructLmMessage, LmStreamHandler
from sr_olthad.agents.planner.prompt import (
    PROMPT_REGISTRY,
    PlannerLmResponseOutputData,
    PlannerPromptInputData,
)
from sr_olthad.config import PlannerCfg as cfg
from sr_olthad.task_node import TaskNode


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


class PlannerReturn(BaseModel):
    output_data: PlannerOutputData


class Planner(Agent):
    def __init__(
        self,
        stream_handler: Optional[LmStreamHandler] = None,
        callback_after_lm_generation_steps: Optional[
            Callable[[List[InstructLmMessage], TaskNode], None]
        ] = None,
    ):
        self.stream_handler = stream_handler
        self.callback_after_lm_generation_steps = (
            callback_after_lm_generation_steps
        )

        planner_prompts = PROMPT_REGISTRY[cfg.PROMPTS_VERSION]
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
        planner_input_data = PlannerPromptInputData(
            env_state=input_data.env_state,
            olthad=input_data.root_task_node.stringify(),
            task_in_question=input_data.current_task_node.stringify(),
        )
        return_obj = await self._planner(
            prompt_template_data=planner_input_data,
            stream_handler=self.stream_handler,
        )
        if self.callback_after_lm_generation_steps is not None:
            self.callback_after_lm_generation_steps(return_obj.messages)
        new_planned_subtasks = return_obj.output_data.new_planned_subtasks
        return PlannerReturn(
            output_data=PlannerOutputData(
                new_planned_subtasks=new_planned_subtasks
            )
        )
