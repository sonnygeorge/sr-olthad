import json
from typing import Callable, Dict, List, Optional

import sr_olthad.config as cfg
from agent_framework.schema import InstructLmMessage, LmStreamHandler
from sr_olthad.agents import (
    AttemptSummarizer,
    AttemptSummarizerInputData,
    Backtracker,
    BacktrackerInputData,
    Forgetter,
    Planner,
)
from sr_olthad.olthad import BacktrackedFromTaskStatus, TaskNode, TaskStatus

# TODO: Handle "notepad" internally? (i.e., decouple internal functions from environment "skills")
# TODO: Results string?
# TODO: Forgetter
# TODO: How to pass callbacks to agents that wait for and process annotator tool inputs

JsonSerializable = (
    None
    | bool
    | int
    | float
    | str
    | List["JsonSerializable"]
    | Dict[str, "JsonSerializable"]
)


class SrOlthad:
    """
    Main class for 'Structured Reasoning with Open-Language Task Hierarchies of Any Depth'
    (sr-OLTHAD).
    """

    def __init__(  # TODO: Docstring
        self,
        highest_level_task: str,
        domain_exposition: str,
        classify_if_action_is_executable: Callable[[str], bool],
        stream_handler: Optional[LmStreamHandler] = None,
        callback_after_each_lm_step: Optional[
            Callable[[List[InstructLmMessage]], None]
        ] = None,
    ):
        # OLTHAD traversal
        self.root_node: TaskNode = TaskNode(
            id="1",
            task=highest_level_task,
            status=TaskStatus.IN_PROGRESS,
            retrospective=None,
            parent_id=None,
        )
        self.cur_node: TaskNode = self.root_node
        self.nodes: Dict[str, TaskNode] = {self.root_node.id: self.root_node}

        # Misc.
        self.domain_exposition = domain_exposition
        self.is_action_executable = classify_if_action_is_executable
        self.has_been_called_at_least_once_before = False

        # Agents
        self.attempt_summarizer = AttemptSummarizer(
            stream_handler=stream_handler,
            callback_after_each_lm_step=callback_after_each_lm_step,
        )
        self.backtracker = Backtracker(
            stream_handler=stream_handler,
            callback_after_each_lm_step=callback_after_each_lm_step,
        )
        self.planner = Planner(
            stream_handler=stream_handler,
            callback_after_each_lm_step=callback_after_each_lm_step,
        )
        self.forgetter = Forgetter(
            stream_handler=stream_handler,
            callback_after_each_lm_step=callback_after_each_lm_step,
        )

    # TODO: Make these methods more idiomatic (w.r.t. their args/return types)

    # async def _backtrack_if_deemed_fit(self, env_state: str) -> bool:
    #     backtracker_input_data = BacktrackerInputData(
    #         env_state=env_state,
    #         root_task_node=self.olthad_traversal.root_node,
    #         current_task_node=self.olthad_traversal.cur_node,
    #     )
    #     backtracker_return = await self.backtracker(backtracker_input_data)
    #     # Backtrack if needed
    #     chosen_status = backtracker_return.output_data.status_to_assign
    #     retrospective = backtracker_return.output_data.retrospective_to_assign
    #     if isinstance(chosen_status, BacktrackedFromTaskStatus):
    #         self.olthad_traversal.backtrack(
    #             chosen_status=chosen_status,
    #             retrospective_to_assign=retrospective,
    #         )
    #         return True
    #     return False

    # # TODO: Optional return for no plan change?
    # async def _update_plan(self, env_state: str) -> None:
    #     planner_input_data = PlannerInputData(
    #         env_state=env_state,
    #         olthad=self.olthad_traversal,
    #     )
    #     # Apply planner with implicit retries
    #     planner_return = await self.planner(planner_input_data)
    #     # TODO: Handle `None` `new_plan`?
    #     self.olthad_traversal.update_planned_subtasks_with_new_planned_subtasks(
    #         new_planned_subtasks=planner_return.output_data.new_plan
    #     )

    async def _process_cur_node_until_next_executable_action_is_determined(
        self, env_state: str
    ) -> None:

        #############################################################
        ## Deliberate backtracking and backtrack if deemed prudent ##
        #############################################################

        # Invoke the backtracker and get outputs
        return_obj = await self.backtracker(
            BacktrackerInputData(
                env_state=env_state,
                root_task_node=self.root_node,
                current_task_node=self.cur_node,
            )
        )
        backtracked_from_status_to_assign = (
            return_obj.output_data.backtracked_from_status_to_assign
        )
        retrospective_to_assign = (
            return_obj.output_data.retrospective_to_assign
        )
        id_of_ancestor_to_backtrack_to = (
            return_obj.output_data.id_of_ancestor_to_backtrack_to
        )

        # Backtrack if needed
        if backtracked_from_status_to_assign is not None:

            # TODO: Remove these asserts
            assert retrospective_to_assign is not None
            assert isinstance(
                backtracked_from_status_to_assign, BacktrackedFromTaskStatus
            )

            # Backtrack our way up to child of this ancestor (pruning subtasks as we go)
            while self.cur_node.parent_id != id_of_ancestor_to_backtrack_to:
                # Prune
                for subtask_node in self.cur_node.subtasks:
                    del self.nodes[subtask_node.id]
                self.cur_node.wipe_subtasks_list()
                # Backtrack
                self.cur_node = self.nodes[self.cur_node.parent_id]

            # Update the status and retrospective of the last child to backtrack from
            self.cur_node.update_status(backtracked_from_status_to_assign)
            self.cur_node.update_retrospective(retrospective_to_assign)

            # Return highest-level-task exit signal if we are to backtrack from the root
            if self.cur_node.parent_id is None:
                return None

            # Backtrack one more time to arrive at the target ancestor
            self.cur_node = self.nodes[self.cur_node.parent_id]

            # Begin processing anew with the new current node
            return self._process_cur_node_until_next_executable_action_is_determined(
                env_state
            )

        # # Planner
        # await self._update_plan(env_state)

        # if self.is_action_executable(
        #     self.olthad_traversal.next_planned_subtask_of_cur_node.description
        # ):  # TODO: "description" is semantically weird here... "task" and "id"?
        #     return (
        #         self.olthad_traversal.next_planned_subtask_of_cur_node.description
        #     )
        # else:
        #     self.olthad_traversal.recurse_inward()
        #     return await self._recursively_deliberate_until_next_executable_action_is_determined(
        #         env_state=env_state
        #     )

    async def __call__(
        self, env_state: str | JsonSerializable
    ) -> Optional[str]:
        """Run the sr-OLTHAD system to get the next executable action (or `None` if
        exiting the highest-level task).

        Args:
            env_state (str | JsonSerializable): The current environment state.

        Returns:
            Optional[str]: The next action, or None if the highest-level task is believed
                to be completed, to been have given an exhaustive (unsuccessful) effort,
                or to be otherwise worth dropping.
        """
        # Stringify env_state if it's not already a string
        if not isinstance(env_state, str):
            env_state = json.dumps(
                env_state, cfg.SrOlthadCfg.JSON_DUMPS_INDENT
            )

        ###################################################
        ## Summarize previous execution (action attempt) ##
        ###################################################

        if not self.has_been_called_at_least_once_before:
            # Initial call, no previous execution/attempt to summarize
            self.has_been_called_at_least_once_before = True
        else:
            # We've completed the attempt of what previously was the next planned subtask
            attempted_subtask_node = self.cur_node.next_planned_subtask
            return_obj = await self.attempt_summarizer(
                AttemptSummarizerInputData(
                    env_state=env_state,
                    root_task_node=self.root_node,
                    attempted_subtask_node=attempted_subtask_node,
                )
            )
            attempted_subtask_node.update_status(
                return_obj.output_data.status_to_assign
            )
            attempted_subtask_node.update_retrospective(
                return_obj.output_data.retrospective_to_assign
            )

        ##########################################################
        ## Enter recursive process to get next action...        ##
        ## (or `None` to signal exit of highest-mode task node) ##
        ##########################################################

        return await self._process_cur_node_until_next_executable_action_is_determined(
            env_state
        )
