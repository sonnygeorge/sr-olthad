from typing import Callable, List, Optional

from loguru import logger
from pydantic import BaseModel

import sr_olthad.config as config
from sr_olthad.enums import AttemptedTaskStatus, BacktrackedFromTaskStatus, TaskStatus
from sr_olthad.agents import (
    AttemptSummarizer,
    AttemptSummarizerInputData,
    Backtracker,
    BacktrackerInputData,
    BacktrackerOutputData,
    BacktrackerReturn,
    Planner,
    PlannerInputData,
    Forgetter,
    ForgetterInputData,
)
from sr_olthad.olthad.task_node import TaskNode
from sr_olthad.olthad.olthad_traversal import OlthadTraversal
from schema import JsonSerializable
from utils import StructuredDataStringifier


# TODO: Handle notepad internally? (i.e., decouple internal functions from environment "skills")
# TODO: Results string?
# TODO: Forgetter
# TODO: How to pass callbacks to agents that wait for and process annotator tool inputs


class SrOlthad:
    """
    Main class for 'Structured Reasoning with Open-Language Task Hierarchies of Any Depth'
    (sr-OLTHAD).
    """

    def __init__(
        self, task_description: str, executable_action_classifier: Callable[[str], bool]
    ):
        self.olthad_traversal = OlthadTraversal(task_description)
        self.has_been_called_at_least_once_before = False
        # Agents
        self.attempt_summarizer = AttemptSummarizer()
        self.backtracker = Backtracker()
        self.planner = Planner()  # TODO: Pass annotator tool callbacks here
        self.forgetter = Forgetter()

    async def _summarize_attempt(self, env_state: str) -> None:
        attempt_summarizer_input = AttemptSummarizerInputData(env_state=env_state)
        attempt_summarizer_return = await self.attempt_summarizer(
            attempt_summarizer_input
        )
        # Update the next-most planned subtask after the attempt summarization
        attempt_status = attempt_summarizer_return.output_data.chosen_status
        attempt_retrospective = attempt_summarizer_return.output_data.retrospective
        self.olthad_traversal.update_next_planned_subtask_after_attempt(
            status=attempt_status, retrospective=attempt_retrospective
        )

    async def _backtrack_if_deemed_fit(self, env_state: str) -> bool:
        backtracker_input_data = BacktrackerInputData(
            env_state=env_state,
            olthad_traversal=self.olthad_traversal,
        )
        backtracker_return = await self.backtracker(backtracker_input_data)
        # Backtrack if needed
        chosen_status = backtracker_return.output_data.chosen_status
        retrospective = backtracker_return.output_data.retrospective
        if isinstance(chosen_status, BacktrackedFromTaskStatus):
            self.olthad_traversal.backtrack(
                chosen_status=chosen_status, retrospective=retrospective
            )
            return True
        return False

    # TODO: Optional return for no plan change?
    async def _update_plan(self, env_state: str) -> None:
        planner_input_data = PlannerInputData(
            env_state=env_state,
            olthad=self.olthad_traversal,
        )
        # Apply planner with implicit retries
        planner_return = await self.planner(planner_input_data)
        # TODO: Handle `None` `new_plan`?
        self.olthad_traversal.update_planned_subtasks(
            new_planned_subtasks=planner_return.output_data.new_plan
        )

    async def _recursively_process_cur_node(self, env_state: str) -> None:
        # Backtracker
        backtracking_occurred = await self._backtrack_if_deemed_fit(env_state)
        if (
            backtracking_occurred
        ):  # TODO: Figure out how to backtrack directly to any ancestor
            # The "current node" has been moved to the parent and we are done processing
            return None  # Backtrack from this recursive call

        # Planner
        await self._update_plan(env_state)

        is_skill = lambda x: "(" in x and ")" in x
        if is_skill(
            self.olthad_traversal.next_planned_subtask_of_cur_node.description
        ):  # TODO: "description" is semantically weird here... "task" and "id"?
            return self.olthad_traversal.next_planned_subtask_of_cur_node.description
        else:
            self.olthad_traversal.recurse_inward()
            return await self._recursively_process_cur_node(env_state=env_state)

    async def __call__(self, env_state: str | JsonSerializable) -> Optional[str]:
        """...

        Returns:
            Optional[str]: The next action, or None if the task is believed to been have
                given an exhaustive effort or be otherwise worth dropping.
        """
        # Stringify env_state if it's not already a string
        if not isinstance(env_state, str):
            env_state = StructuredDataStringifier.stringify(
                env_state,
                serialization_method=config.STRINGIFY_ENV_STATE_SERIALIZATION_METHOD,
            )

        # Summarize previous attempt unless it's the initial call
        # (in which case, there's no previous attempt to summarize)
        if self.has_been_called_at_least_once_before:
            self._summarize_attempt(env_state)
        else:
            self.has_been_called_at_least_once_before = True

        return await self._recursively_process_cur_node(env_state)
