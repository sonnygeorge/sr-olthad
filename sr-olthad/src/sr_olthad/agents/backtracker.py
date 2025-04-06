from sr_olthad.common.agents import InstructLmAgent, InstructLmAgentOutput
from sr_olthad.common.schema import LmStreamsHandler
from sr_olthad.config import BacktrackerCfg as cfg
from sr_olthad.lm_step import LmStepTemplate
from sr_olthad.olthad import OlthadTraversal, PendingOlthadUpdate
from sr_olthad.prompts import (
    WAS_SUCCESSFULLY_COMPLETED_OPTIONS,
    BacktrackerSubAgentLmResponseOutputData,
)
from sr_olthad.schema import (
    BacktrackedFromTaskStatus,
    CommonUserPromptInputData,
    LmAgentName,
)
from sr_olthad.utils import extract_letter_from_multiple_choice_response


# NOTE: Implementation of protocol `AggregateWinningVoteReasons` (must have these kwargs in this order)
def get_first_of_winning_reasons(
    winning_reasons: list[str], winner: str, num_winning_votes: int, num_total_votes: int
) -> str:
    """
    Implements an AggregateWinningVoteReasons strategy that: in the case of self-consistency
    'voting', simply selects the first winning reasons as the 'aggregated' reason string.
    """
    return winning_reasons[0]


# NOTE: Implementation of protocol `AggregateWinningVoteReasons` (must have these kwargs in this order)
def get_longest_of_winning_reasons(
    winning_reasons: list[str], winner: str, num_winning_votes: int, num_total_votes: int
) -> str:
    """
    Implements an AggregateWinningVoteReasons strategy that: in the case of self-consistency
    'voting', selects the longest winning reason as the 'aggregated' reason string.

    If multiple reasons share the maximum length, the first such reason is returned.
    """
    return max(winning_reasons, key=len)


class Backtracker:
    """The backtracker in the sr-OLTHAD system."""

    def __init__(
        self,
        olthad_traversal: OlthadTraversal,
        lm_step_template: LmStepTemplate,
        streams_handler: LmStreamsHandler | None = None,
    ):
        super().__init__()

        self.traversal = olthad_traversal
        self.lm_step_template = lm_step_template

        ###############################################
        ### Initialize exhaustive effort classifier ###
        ###############################################

        self.exhaustive_effort_clf: InstructLmAgent[
            BacktrackerSubAgentLmResponseOutputData
        ] = InstructLmAgent(
            instruct_lm=cfg.ExhaustiveEffortClf.INSTRUCT_LM,
            response_json_model=BacktrackerSubAgentLmResponseOutputData,
            max_tries_to_get_parsable_response=cfg.ExhaustiveEffortClf.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
            num_calls_for_voting=cfg.ExhaustiveEffortClf.N_CALLS_FOR_VOTING,
            max_async_calls=cfg.ExhaustiveEffortClf.MAX_ASYNC_CALLS_FOR_VOTING,
            vote_field=BacktrackerSubAgentLmResponseOutputData.answer_attr,
            reason_field=BacktrackerSubAgentLmResponseOutputData.retrospective_attr,
            streams_handler=streams_handler,
            aggregate_winning_vote_reasons=get_longest_of_winning_reasons,
        )

        #####################################################
        ### Initialize most worthwhile pursuit classifier ###
        #####################################################

        self.most_worthwhile_pursuit_clf: InstructLmAgent[
            BacktrackerSubAgentLmResponseOutputData
        ] = InstructLmAgent(
            instruct_lm=cfg.MostWorthwhilePursuitClfCfg.INSTRUCT_LM,
            response_json_model=BacktrackerSubAgentLmResponseOutputData,
            max_tries_to_get_parsable_response=cfg.MostWorthwhilePursuitClfCfg.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
            num_calls_for_voting=cfg.MostWorthwhilePursuitClfCfg.N_CALLS_FOR_VOTING,
            max_async_calls=cfg.MostWorthwhilePursuitClfCfg.MAX_ASYNC_CALLS_FOR_VOTING,
            vote_field=BacktrackerSubAgentLmResponseOutputData.answer_attr,
            reason_field=BacktrackerSubAgentLmResponseOutputData.retrospective_attr,
            streams_handler=streams_handler,
            aggregate_winning_vote_reasons=get_longest_of_winning_reasons,
        )

        #############################################
        ### Initialize partial success classifier ###
        #############################################

        self.partial_success_clf: InstructLmAgent[
            BacktrackerSubAgentLmResponseOutputData
        ] = InstructLmAgent(
            instruct_lm=cfg.PartialSuccessClfCfg.INSTRUCT_LM,
            response_json_model=BacktrackerSubAgentLmResponseOutputData,
            max_tries_to_get_parsable_response=cfg.PartialSuccessClfCfg.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
            num_calls_for_voting=cfg.PartialSuccessClfCfg.N_CALLS_FOR_VOTING,
            max_async_calls=cfg.PartialSuccessClfCfg.MAX_ASYNC_CALLS_FOR_VOTING,
            vote_field=BacktrackerSubAgentLmResponseOutputData.answer_attr,
            reason_field=BacktrackerSubAgentLmResponseOutputData.retrospective_attr,
            streams_handler=streams_handler,
            aggregate_winning_vote_reasons=get_longest_of_winning_reasons,
        )

        ###################################################
        ### Initialize successful completion classifier ###
        ###################################################

        self.successful_completion_clf: InstructLmAgent[
            BacktrackerSubAgentLmResponseOutputData
        ] = InstructLmAgent(
            instruct_lm=cfg.SuccessfulCompletionClfCfg.INSTRUCT_LM,
            response_json_model=BacktrackerSubAgentLmResponseOutputData,
            max_tries_to_get_parsable_response=cfg.SuccessfulCompletionClfCfg.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
            num_calls_for_voting=cfg.SuccessfulCompletionClfCfg.N_CALLS_FOR_VOTING,
            max_async_calls=cfg.SuccessfulCompletionClfCfg.MAX_ASYNC_CALLS_FOR_VOTING,
            vote_field=BacktrackerSubAgentLmResponseOutputData.answer_attr,
            reason_field=BacktrackerSubAgentLmResponseOutputData.retrospective_attr,
            streams_handler=streams_handler,
            aggregate_winning_vote_reasons=get_longest_of_winning_reasons,
        )

    def _process_successful_completion_clf_output(
        self, output: InstructLmAgentOutput[BacktrackerSubAgentLmResponseOutputData]
    ) -> tuple[bool, PendingOlthadUpdate]:
        lm_choice = extract_letter_from_multiple_choice_response(
            output.data.answer,
            WAS_SUCCESSFULLY_COMPLETED_OPTIONS,
        )
        if lm_choice == WAS_SUCCESSFULLY_COMPLETED_OPTIONS[True].letter:
            return True, self.traversal.update_status_and_retrospective_of(
                node=self.traversal.cur_node,
                new_status=BacktrackedFromTaskStatus.SUCCESS,
                new_retrospective=output.data.retrospective,
            )
        else:
            return False, self.traversal.update_nothing()

    async def run(self, env_state: str) -> bool | None:
        """
        Runs the backtracker.

        Returns:
            bool: Whether backtracking occured.
        """

        # Prepare prompt input used by all classifiers except most_worthwhile_pursuit_clf
        prompt_input_data = CommonUserPromptInputData(
            env_state=env_state,
            olthad=self.traversal._root_node.stringify(
                redact_planned_subtasks_below=self.traversal.cur_node.id,
                obfuscate_status_of=self.traversal.cur_node.id,
            ),
            task_in_question=self.traversal._cur_node.stringify(
                redact_planned_subtasks_below=self.traversal.cur_node.id,
                obfuscate_status_of=self.traversal.cur_node.id,
            ),
        )

        ##########################################################################
        ### LM STEP: Classify whether the task has been successfully completed ###
        ##########################################################################

        lm_agent_name = LmAgentName.SUCCESSFUL_COMPLETION_CLF

        # Compose lm step
        lm_step = self.lm_step_template.compose(
            run_step=self.successful_completion_clf.run,
            process_output=self._process_successful_completion_clf_output,
            lm_agent_name=lm_agent_name,
            cur_node_id=self.traversal.cur_node.id,
            prompt_input_data=prompt_input_data,
            n_streams_to_handle=cfg.SuccessfulCompletionClfCfg.N_CALLS_FOR_VOTING,
        )

        # Run lm step
        cur_task_was_deemed_successfully_completed = await lm_step()
        if cur_task_was_deemed_successfully_completed:
            # Backtrack to the parent of the current node
            self.traversal.backtrack_to(self.traversal.cur_node.parent_id)
            # Return True to indicate that backtracking occurred
            return True

        ##############################################################################
        ### LM STEP: Classify whether the task has been given an exhaustive effort ###
        ##############################################################################

        raise NotImplementedError

        # ...

        # if lm_choice == EFFORT_WAS_EXHAUSTIVE_OPTIONS[True].letter:

        #     ######################################################################
        #     ### LM STEP: Classify whether the completion was a partial success ###
        #     ######################################################################

        #     ...

        # else:  # Effort was not deemed exhaustive

        #     #######################################################################################
        #     ### LM STEP(S): Classify if ancestor tasks are (still) the most worthwhile pursuits ###
        #     #######################################################################################

        #     for (  # Iter through gradual reconstruction of olthad starting from cur=root
        #         root_node,
        #         cur_node,
        #     ) in input_data.root_task_node.iter_in_progress_descendants():

        #         ...

        #         if choice == IS_MOST_WORTHWHILE_OPTIONS[False].letter:
        #             # Backtrack to the this node

        #     # Finally, if ancestors are still deemed worthwhile, no backtracking warranted
