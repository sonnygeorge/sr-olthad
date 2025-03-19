import json
from typing import Callable, Dict, List, Optional

import sr_olthad.config as cfg
from agent_framework.schema import LmStreamsHandler
from sr_olthad.agents import (
    AttemptSummarizer,
    Backtracker,
    Forgetter,
    Planner,
    PlannerInputData,
)
from sr_olthad.emissions import (
    PostLmGenerationStepHandler,
    PreLmGenerationStepHandler,
)
from sr_olthad.olthad import (
    BacktrackedFromTaskStatus,
    OlthadTraversal,
    TaskNode,
    TaskStatus,
)

# TODO: Remove prints
# TODO: Handle "notepad" internally? (i.e., decouple internal functions from environment "skills")
# TODO: Results string?
# TODO: Forgetter


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
        domain_documentation: str,
        highest_level_task: str,
        classify_if_task_is_executable_action: Callable[[str], bool],
        pre_lm_generation_step_handler: Optional[
            PreLmGenerationStepHandler
        ] = None,
        post_lm_generation_step_handler: Optional[
            PostLmGenerationStepHandler
        ] = None,
        streams_handler: Optional[LmStreamsHandler] = None,
    ):
        if streams_handler is not None and not isinstance(
            streams_handler, LmStreamsHandler
        ):
            raise ValueError(
                "The `streams_handler` must inherit from the `LmStreamsHandler` ABC."
            )

        # OLTHAD traversal
        root_node = TaskNode(
            id="1",
            task=highest_level_task,
            status=TaskStatus.IN_PROGRESS,
            retrospective=None,
            parent_id=None,
        )
        self.traversal = OlthadTraversal(
            root_node=root_node,
            cur_node=root_node,
            nodes={root_node.id: root_node},
        )

        # Misc.
        self.domain_documentation = domain_documentation
        self.is_task_executable_action = classify_if_task_is_executable_action
        self.has_been_called_at_least_once_before = False

        # Agents
        self.attempt_summarizer = AttemptSummarizer(
            olthad_traversal=self.traversal,
            pre_lm_generation_step_handler=pre_lm_generation_step_handler,
            post_lm_generation_step_handler=post_lm_generation_step_handler,
            streams_handler=streams_handler,
        )
        self.backtracker = Backtracker(
            olthad_traversal=self.traversal,
            pre_lm_generation_step_handler=pre_lm_generation_step_handler,
            post_lm_generation_step_handler=post_lm_generation_step_handler,
            streams_handler=streams_handler,
        )
        self.planner = Planner(
            olthad_traversal=self.traversal,
            pre_lm_generation_step_handler=pre_lm_generation_step_handler,
            post_lm_generation_step_handler=post_lm_generation_step_handler,
            streams_handler=streams_handler,
        )
        self.forgetter = Forgetter(
            olthad_traversal=self.traversal,
            pre_lm_generation_step_handler=pre_lm_generation_step_handler,
            post_lm_generation_step_handler=post_lm_generation_step_handler,
            streams_handler=streams_handler,
        )

    async def _process_cur_node_until_next_executable_action_is_determined(
        self, env_state: str
    ) -> None:

        if self.has_been_called_at_least_once_before:
            #############################################################
            ## Deliberate backtracking and backtrack if deemed prudent ##
            #############################################################

            # Invoke the backtracker and get outputs
            return_obj = await self.backtracker(env_state=env_state)
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
                    backtracked_from_status_to_assign,
                    BacktrackedFromTaskStatus,
                )

                # Backtrack our way up to child of this ancestor (pruning subtasks as we go)
                while (
                    self.cur_node.parent_id != id_of_ancestor_to_backtrack_to
                ):
                    # Prune from the nodes dict
                    for subtask_node in self.cur_node.subtasks:
                        del self.nodes[subtask_node.id]
                    self.cur_node.remove_subtasks()
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
                return await self._process_cur_node_until_next_executable_action_is_determined(
                    env_state
                )

        #########################################
        ## Update tentatively planned subtasks ##
        #########################################

        planner_input_data = PlannerInputData(
            env_state=env_state,
            root_task_node=self.root_node,
            current_task_node=self.cur_node,
        )
        return_obj = await self.planner(planner_input_data)
        new_planned_subtasks = return_obj.output_data.new_planned_subtasks
        if len(new_planned_subtasks) == 0:
            raise NotImplementedError(
                "The planner returning no new planned subtasks is not yet handled."
            )
        new_planned_subtask_nodes = []
        for i, new_planned_subtask in enumerate(new_planned_subtasks):
            new_subtask_node = TaskNode(
                id=f"{self.cur_node.id}.{i+1}",
                parent_id=self.cur_node.id,
                task=new_planned_subtask,
                status=TaskStatus.PLANNED,
                retrospective=None,
            )
            new_planned_subtask_nodes.append(new_subtask_node)
        self.cur_node.update_planned_subtasks(
            new_planned_subtasks=new_planned_subtask_nodes
        )

        if self.is_task_executable_action(
            self.cur_node.next_planned_subtask.task
        ):
            return self.cur_node.next_planned_subtask.task
        else:
            # Recurse inward to break down the next planned subtask
            self.cur_node = self.cur_node.next_planned_subtask
            return await self._process_cur_node_until_next_executable_action_is_determined(
                env_state
            )

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

        # if self.has_been_called_at_least_once_before:
        #     await self.attempt_summarizer(env_state=env_state)

        ##########################################################
        ## Enter recursive process to get next action...        ##
        ## (or `None` to signal exit of highest-mode task node) ##
        ##########################################################

        output = await self._process_cur_node_until_next_executable_action_is_determined(
            env_state
        )
        self.has_been_called_at_least_once_before = True
        # print("#" * 80)
        # print("#" * 80, "\n\n")
        # print(self.root_node.stringify())
        # print("\n\n", "#" * 80)
        # print("#" * 80)
        return output
