import json
from collections.abc import Callable

import sr_olthad.config as cfg
from sr_olthad.agents import AttemptSummarizer, Backtracker, Forgetter, Planner
from sr_olthad.framework.agents import LmRetryHandler
from sr_olthad.framework.schema import LmStreamsHandler
from sr_olthad.framework.utils import call_or_await
from sr_olthad.lm_step import (
    LmStepTemplate,
    PostLmStepApprover,
    PreLmStepHandler,
)
from sr_olthad.olthad import OlthadTraversal
from sr_olthad.schema import GetDomainSpecificSysPromptInputData, TaskStatus

# TODO: Forgetter(?)


# TODO: The idea of calling the next-most planned subtask in-progress is semantically wrong.
# TODO: Furthermore, when we hit the planner on the second go-around, we have an awkward in-progress
# subtask that's really a planned subtask.
# TODO: Recurse inward is the only thing that should set something to in-progress.

JsonSerializable = (
    None
    | bool
    | int
    | float
    | str
    | list["JsonSerializable"]
    | dict[str, "JsonSerializable"]
)


class SrOlthad:
    """
    Main class for 'Structured Reasoning with Open-Language Task Hierarchies of Any Depth'
    (sr-OLTHAD).
    """

    def __init__(  # TODO: Docstring w/ descriptions for all params/args
        self,
        highest_level_task: str,
        is_task_executable_skill_invocation: Callable[[str], bool],
        pre_lm_step_handler: PreLmStepHandler = lambda _: None,
        lm_retry_handler: LmRetryHandler = lambda _, __: None,
        post_lm_step_approver: PostLmStepApprover = lambda _: True,
        # TODO: Make this non-optional since sr-OLTHAD will never been run w/out domains?
        # ...or keep it optional for _true_ plug-and-play to enable seeing if the LM can
        # just infer good plans/actions without explicit domain exposition?
        get_domain_specific_sys_prompt_input_data: GetDomainSpecificSysPromptInputData
        | None = None,
        streams_handler: LmStreamsHandler | None = None,
    ):
        super().__init__()

        self.traversal = OlthadTraversal(highest_level_task=highest_level_task)
        self.is_task_executable_skill_invocation = is_task_executable_skill_invocation
        self.has_been_called_at_least_once_before = False

        lm_step_template = LmStepTemplate(
            pre_lm_step_handler=pre_lm_step_handler,
            lm_retry_handler=lm_retry_handler,
            post_lm_step_approver=post_lm_step_approver,
            get_domain_specific_sys_prompt_input_data=get_domain_specific_sys_prompt_input_data,
        )

        self.attempt_summarizer = AttemptSummarizer(
            olthad_traversal=self.traversal,
            lm_step_template=lm_step_template,
            streams_handler=streams_handler,
        )
        self.backtracker = Backtracker(
            olthad_traversal=self.traversal,
            lm_step_template=lm_step_template,
            streams_handler=streams_handler,
        )
        self.planner = Planner(
            olthad_traversal=self.traversal,
            lm_step_template=lm_step_template,
            streams_handler=streams_handler,
        )
        self.forgetter = Forgetter(
            olthad_traversal=self.traversal,
            lm_step_template=lm_step_template,
            streams_handler=streams_handler,
        )

    async def _traverse_and_get_next_skill_invocation(self, env_state: str) -> str | None:
        if (
            self.has_been_called_at_least_once_before
            or self.traversal.cur_node.parent_id == self.traversal.root_node.id
        ):
            #############################################################
            ## Deliberate backtracking and backtrack if deemed prudent ##
            #############################################################

            # Invoke the backtracker and get outputs
            did_backtrack = await self.backtracker.run(env_state=env_state)
            if did_backtrack:
                # Check if we backtracked out of root
                if self.traversal.cur_node is None:
                    # If so, propogate signal that there is no next action
                    return None
                # Otherwise restart this function with the new current node
                return await self._traverse_and_get_next_skill_invocation(env_state)

        #########################################
        ## Update tentatively planned subtasks ##
        #########################################

        await self.planner.run(env_state=env_state)

        #################################################################################
        ## Check if the next of the planned subtasks is an executable skill invocation ##
        #################################################################################

        if await call_or_await(
            self.is_task_executable_skill_invocation,
            self.traversal.cur_node.next_planned_subtask.task,
        ):
            # Time to invoke this skill in the env (set status to in-progress and return)
            self.traversal.update_status_and_retrospective_of(
                self.traversal.cur_node.next_planned_subtask,
                TaskStatus.IN_PROGRESS,
            ).commit()
            return self.traversal.cur_node.in_progress_subtask.task
        else:
            self.traversal.recurse_inward()
            return await self._traverse_and_get_next_skill_invocation(env_state)

    async def get_next_skill_invocation(
        self, env_state: str | JsonSerializable
    ) -> str | None:
        """
        Run the sr-OLTHAD system to get the next "skill" invocation (i.e., executable
        action specification) (or `None` if exiting the highest-level task).

        Args:
            env_state (str | JsonSerializable): The current environment state.

        Returns:
            str | None: The next "skill invocation" (i.e. executable action spec), or None
                if the highest-level task is believed to be completed, to been have given
                an exhaustive (unsuccessful) effort, or to be otherwise worth dropping.
        """
        # Stringify env_state if it's not already a string
        if not isinstance(env_state, str):
            env_state = json.dumps(env_state, cfg.SrOlthadCfg.JSON_DUMPS_INDENT)

        if self.has_been_called_at_least_once_before:
            # Summarize previous execution (action attempt)
            await self.attempt_summarizer.run(env_state=env_state)

        # Enter recursive process to get next action (or `None` to signal exit of
        # highest-level task/root OLTHAD node)
        next_skill_invocation = await self._traverse_and_get_next_skill_invocation(env_state)

        self.has_been_called_at_least_once_before = True
        return next_skill_invocation
