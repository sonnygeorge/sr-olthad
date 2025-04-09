import functools

from sr_olthad.config import BacktrackerCfg as cfg
from sr_olthad.framework.agents import InstructLmAgent, InstructLmAgentOutput
from sr_olthad.framework.schema import LmStreamsHandler
from sr_olthad.lm_step import LmStepTemplate
from sr_olthad.olthad import OlthadTraversal, PendingOlthadUpdate, TaskNode
from sr_olthad.prompts import (
    EFFORT_WAS_EXHAUSTIVE_OPTIONS,
    IS_MOST_WORTHWHILE_PURSUIT_OPTIONS,
    WAS_PARTIAL_SUCCESS_OPTIONS,
    WAS_SUCCESSFULLY_COMPLETED_OPTIONS,
    BacktrackerSubAgentLmResponseOutputData,
)
from sr_olthad.schema import (
    BacktrackedFromTaskStatus,
    LmAgentName,
    UserPromptInputData,
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

    def _process_successful_completion_clf_output(
        self, output: InstructLmAgentOutput[BacktrackerSubAgentLmResponseOutputData]
    ) -> tuple[bool, PendingOlthadUpdate]:
        """
        Processes the output of the successful completion classifier.

        Args:
            output (InstructLmAgentOutput[BacktrackerSubAgentLmResponseOutputData]):
                The output of the successful completion classifier.

        Returns:
            bool: Whether the task was deemed to have been successfully completed.
            PendingOlthadUpdate: The update to be applied to the OLTHAD traversal.
        """
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

    def _process_exhaustive_effort_clf_output(
        self,
        output: InstructLmAgentOutput[BacktrackerSubAgentLmResponseOutputData],
    ) -> tuple[bool, PendingOlthadUpdate]:
        """
        Processes the output of the exhaustive effort classifier.

        Args:
            output (InstructLmAgentOutput[BacktrackerSubAgentLmResponseOutputData]):
                The output of the exhaustive effort classifier.

        Returns:
            bool: Whether the task was deemed to have been given exhaustive effort.
            PendingOlthadUpdate: The update to be applied to the OLTHAD traversal.
        """
        lm_choice = extract_letter_from_multiple_choice_response(
            output.data.answer,
            EFFORT_WAS_EXHAUSTIVE_OPTIONS,
        )
        if lm_choice == EFFORT_WAS_EXHAUSTIVE_OPTIONS[True].letter:
            return True, self.traversal.update_nothing()
        else:
            return False, self.traversal.update_nothing()

    def _process_partial_success_clf_output(
        self,
        output: InstructLmAgentOutput[BacktrackerSubAgentLmResponseOutputData],
    ) -> tuple[bool, PendingOlthadUpdate]:
        """
        Processes the output of the partial success classifier.

        Args:
            output (InstructLmAgentOutput[BacktrackerSubAgentLmResponseOutputData]):
                The output of the partial success classifier.

        Returns:
            bool: Whether the task was deemed to be a partial success.
            PendingOlthadUpdate: The update to be applied to the OLTHAD traversal.
        """
        lm_choice = extract_letter_from_multiple_choice_response(
            output.data.answer,
            WAS_PARTIAL_SUCCESS_OPTIONS,
        )
        if lm_choice == WAS_PARTIAL_SUCCESS_OPTIONS[True].letter:
            return True, self.traversal.update_status_and_retrospective_of(
                node=self.traversal.cur_node,
                new_status=BacktrackedFromTaskStatus.PARTIAL_SUCCESS,
                new_retrospective=output.data.retrospective,
            )
        else:
            return False, self.traversal.update_status_and_retrospective_of(
                node=self.traversal.cur_node,
                new_status=BacktrackedFromTaskStatus.FAILURE,
                new_retrospective=output.data.retrospective,
            )

    def _process_most_worthwhile_pursuit_clf_output(
        self,
        output: InstructLmAgentOutput[BacktrackerSubAgentLmResponseOutputData],
        node_to_update: TaskNode,
    ) -> tuple[bool, PendingOlthadUpdate]:
        """
        Processes the output of the most worthwhile pursuit classifier.

        Args:
            output (InstructLmAgentOutput[BacktrackerSubAgentLmResponseOutputData]):
                The output of the most worthwhile pursuit classifier.
            node_to_update (TaskNode): The task node to update. NOTE: This argument should
                be pre-applied before passing this function to the lm_step_template.

        Returns:
            bool: Whether the task was deemed to be the most worthwhile pursuit.
            PendingOlthadUpdate: The update to be applied to the OLTHAD traversal.
        """
        lm_choice = extract_letter_from_multiple_choice_response(
            output.data.answer,
            IS_MOST_WORTHWHILE_PURSUIT_OPTIONS,
        )
        if lm_choice == IS_MOST_WORTHWHILE_PURSUIT_OPTIONS[True].letter:
            return True, self.traversal.update_nothing()
        else:
            return False, self.traversal.update_status_and_retrospective_of(
                node=node_to_update,
                new_status=BacktrackedFromTaskStatus.DROPPED,
                new_retrospective=output.data.retrospective,
            )

    async def run(self, env_state: str) -> bool | None:
        """
        Runs the backtracker.

        Args:
            env_state (str): The current environment state.

        Returns:
            bool: Whether backtracking occured.
        """

        # Prepare prompt input used by all classifiers except most_worthwhile_pursuit_clf
        prompt_input_data = UserPromptInputData(
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

        # Compose lm step
        lm_step = self.lm_step_template.compose(
            run_step=self.successful_completion_clf.run,
            process_output=self._process_successful_completion_clf_output,
            lm_agent_name=LmAgentName.SUCCESSFUL_COMPLETION_CLF,
            cur_node_id=self.traversal.cur_node.id,
            prompt_input_data=prompt_input_data,
            n_streams_to_handle=cfg.SuccessfulCompletionClfCfg.N_CALLS_FOR_VOTING,
        )

        # Run lm step
        cur_task_was_deemed_successfully_completed = await lm_step()

        # React to lm step result
        if cur_task_was_deemed_successfully_completed:
            # Backtrack to the parent of the current node
            self.traversal.backtrack_to(self.traversal.cur_node.parent_id)
            return True  # Return True to indicate that backtracking occurred

        ##############################################################################
        ### LM STEP: Classify whether the task has been given an exhaustive effort ###
        ##############################################################################

        # Compose lm step
        lm_step = self.lm_step_template.compose(
            run_step=self.exhaustive_effort_clf.run,
            process_output=self._process_successful_completion_clf_output,
            lm_agent_name=LmAgentName.EXHAUSTIVE_EFFORT_CLF,
            cur_node_id=self.traversal.cur_node.id,
            prompt_input_data=prompt_input_data,
            n_streams_to_handle=cfg.ExhaustiveEffortClf.N_CALLS_FOR_VOTING,
        )

        # Run lm step
        cur_task_was_deemed_to_have_been_given_exhaustive_effort = await lm_step()

        # React to lm step result
        if cur_task_was_deemed_to_have_been_given_exhaustive_effort:
            ######################################################################
            ### LM STEP: Classify whether the completion was a partial success ###
            ######################################################################

            # Compose lm step
            lm_step = self.lm_step_template.compose(
                run_step=self.partial_success_clf.run,
                process_output=self._process_partial_success_clf_output,
                lm_agent_name=LmAgentName.PARTIAL_SUCCESS_CLF,
                cur_node_id=self.traversal.cur_node.id,
                prompt_input_data=prompt_input_data,
                n_streams_to_handle=cfg.PartialSuccessClfCfg.N_CALLS_FOR_VOTING,
            )

            # Run lm step
            cur_task_was_deemed_to_have_been_a_partial_success = await lm_step()  # noqa: F841

            # React to lm step result (always backtrack)
            # Backtrack to the parent of the current node
            self.traversal.backtrack_to(self.traversal.cur_node.parent_id)
            return True  # Return True to indicate that backtracking occurred

        else:  # Effort was not deemed exhaustive
            #######################################################################################
            ### LM STEP(S): Classify if ancestor tasks are (still) the most worthwhile pursuits ###
            #######################################################################################

            for (  # Iter through gradual reconstruction of olthad starting from cur=root
                root_node_reconstructed_copy,
                cur_node_reconstructed_copy,
                cur_node_original,
            ) in self.traversal.root_node.iter_in_progress_descendants():
                prompt_input_data = UserPromptInputData(
                    env_state=env_state,
                    olthad=root_node_reconstructed_copy.stringify(
                        redact_planned_subtasks_below=cur_node_reconstructed_copy.id,
                        obfuscate_status_of=cur_node_reconstructed_copy.id,
                    ),
                    task_in_question=cur_node_reconstructed_copy.stringify(
                        redact_planned_subtasks_below=cur_node_reconstructed_copy.id,
                        obfuscate_status_of=cur_node_reconstructed_copy.id,
                    ),
                )

                # Compose lm step
                lm_step = self.lm_step_template.compose(
                    run_step=self.most_worthwhile_pursuit_clf.run,
                    # NOTE: We pre-apply the node_to_update argument so that
                    # self._process_most_worthwhile_pursuit_clf_output matches the
                    # signature expected by lm_step_template.
                    process_output=functools.partial(
                        self._process_most_worthwhile_pursuit_clf_output,
                        node_to_update=cur_node_original,
                    ),
                    lm_agent_name=LmAgentName.MOST_WORTHWHILE_PURSUIT_CLF,
                    cur_node_id=cur_node_reconstructed_copy.id,
                    prompt_input_data=prompt_input_data,
                    n_streams_to_handle=cfg.MostWorthwhilePursuitClfCfg.N_CALLS_FOR_VOTING,
                )

                # Run lm step
                cur_task_was_deemed_to_still_be_the_most_worthwhile_pursuit = await lm_step()

                # React to lm step result
                if not cur_task_was_deemed_to_still_be_the_most_worthwhile_pursuit:
                    # Backtrack to the parent of this current node in the gradual reconstruction
                    self.traversal.backtrack_to(cur_node_reconstructed_copy.parent_id)
                    return True

            # Finally, if ancestors (including cur task in question) are still deemed
            # worthwhile, indicate that no backtracking occurred
            return False
