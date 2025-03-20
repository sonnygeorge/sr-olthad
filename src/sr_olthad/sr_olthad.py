import json
from typing import Callable, Dict, List, Optional

import sr_olthad.config as cfg
from agent_framework.schema import LmStreamsHandler
from sr_olthad.agents import AttemptSummarizer, Backtracker, Forgetter, Planner
from sr_olthad.emissions import (
    PostLmGenerationStepHandlerAndApprover,
    PreLmGenerationStepHandler,
)
from sr_olthad.olthad import OlthadTraversal

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
        pre_lm_generation_step_handler: Optional[PreLmGenerationStepHandler] = None,
        post_lm_generation_step_approver: Optional[
            PostLmGenerationStepHandlerAndApprover
        ] = None,
        streams_handler: Optional[LmStreamsHandler] = None,
    ):
        if streams_handler is not None and not isinstance(streams_handler, LmStreamsHandler):
            msg = "`streams_handler` must inherit from the `LmStreamsHandler` ABC."
            raise ValueError(msg)

        self.traversal = OlthadTraversal(highest_level_task=highest_level_task)
        self.domain_documentation = domain_documentation  # TODO: Use
        self.is_task_executable_action = classify_if_task_is_executable_action
        self.has_been_called_at_least_once_before = False

        # Agents
        self.attempt_summarizer = AttemptSummarizer(
            olthad_traversal=self.traversal,
            pre_lm_generation_step_handler=pre_lm_generation_step_handler,
            post_lm_generation_step_handler=post_lm_generation_step_approver,
            streams_handler=streams_handler,
        )
        self.backtracker = Backtracker(
            olthad_traversal=self.traversal,
            pre_lm_generation_step_handler=pre_lm_generation_step_handler,
            post_lm_generation_step_handler=post_lm_generation_step_approver,
            streams_handler=streams_handler,
        )
        self.planner = Planner(
            olthad_traversal=self.traversal,
            pre_lm_generation_step_handler=pre_lm_generation_step_handler,
            post_lm_generation_step_handler=post_lm_generation_step_approver,
            streams_handler=streams_handler,
        )
        self.forgetter = Forgetter(
            olthad_traversal=self.traversal,
            pre_lm_generation_step_handler=pre_lm_generation_step_handler,
            post_lm_generation_step_handler=post_lm_generation_step_approver,
            streams_handler=streams_handler,
        )

    async def _traverse_and_get_executable_action(self, env_state: str) -> None:

        if self.has_been_called_at_least_once_before:
            #############################################################
            ## Deliberate backtracking and backtrack if deemed prudent ##
            #############################################################

            # Invoke the backtracker and get outputs
            did_backtrack = await self.backtracker(env_state=env_state)
            if did_backtrack:
                # Check if we backtracked out of root
                if self.traversal.cur_node is None:
                    # If so, propogate signal that there is no next action
                    return None
                # Otherwise restart processing anew with the new current node
                return await self._traverse_and_get_executable_action(env_state)

        #########################################
        ## Update tentatively planned subtasks ##
        #########################################

        raise NotImplementedError

        # ...

        #########################################################################
        ## Check if the next of these planned subtasks is an executable action ##
        #########################################################################

        # if self.is_task_executable_action(
        #     self.traversal.cur_node.in_progress_subtask.task
        # ):
        #     self.traversal.cur_node.in_progress_subtask.task
        # else:
        #     self.traversal.recurse_inward()
        #     return await _traverse_and_get_executable_action(env_state)

    async def __call__(self, env_state: str | JsonSerializable) -> str | None:
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
            env_state = json.dumps(env_state, cfg.SrOlthadCfg.JSON_DUMPS_INDENT)

        # if self.has_been_called_at_least_once_before:
        #     # Summarize previous execution (action attempt)
        #     await self.attempt_summarizer(env_state=env_state)

        # Enter recursive process to get next action (or `None` to signal exit of
        # highest-level task/root OLTHAD node)
        next_executable_action = await self._traverse_and_get_executable_action(env_state)

        self.has_been_called_at_least_once_before = True
        return next_executable_action
