from typing import Callable, Optional

from loguru import logger

from agent_framework.agents import InstructLmChatAgent
from agent_framework.schema import Agent, LmStreamsHandler
from agent_framework.utils import (
    render_single_turn_prompt_templates_and_get_messages,
    with_implicit_async_voting,
)
from sr_olthad.agents.backtracker.prompt import (
    SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY,
    WAS_SUCCESSFULLY_COMPLETED_OPTIONS,
    BacktrackerSubAgentLmResponseOutputData,
    BacktrackerSubAgentOutputFields,
    BacktrackerSubAgentPromptInputData,
)
from sr_olthad.config import BacktrackerCfg as cfg
from sr_olthad.emissions import (
    PostLmGenerationStepEmission,
    PostLmGenerationStepHandlerAndApprover,
    PreLmGenerationStepEmission,
    PreLmGenerationStepHandler,
)
from sr_olthad.olthad import BacktrackedFromTaskStatus, OlthadTraversal
from sr_olthad.schema import AgentName
from sr_olthad.utils import (
    call_or_await,
    extract_letter_from_multiple_choice_question_response,
)


class Backtracker(Agent):
    """
    The backtracker agent in the sr-OLTHAD system.
    """

    def __init__(
        self,
        olthad_traversal: OlthadTraversal,
        pre_lm_generation_step_handler: Optional[PreLmGenerationStepHandler] = None,
        post_lm_generation_step_handler: Optional[
            PostLmGenerationStepHandlerAndApprover
        ] = None,
        streams_handler: Optional[LmStreamsHandler] = None,
    ):
        self.traversal = olthad_traversal
        self.streams_handler = streams_handler
        self.pre_lm_step_handler = pre_lm_generation_step_handler
        self.post_lm_step_approver = post_lm_generation_step_handler

        ###############################################
        ### Initialize exhaustive effort classifier ###
        ###############################################

        self.exhaustive_effort_clf: InstructLmChatAgent[
            BacktrackerSubAgentLmResponseOutputData
        ] = InstructLmChatAgent(
            instruct_lm=cfg.ExhaustiveEffortClf.INSTRUCT_LM,
            response_json_data_model=BacktrackerSubAgentLmResponseOutputData,
            max_tries_to_get_valid_response=cfg.ExhaustiveEffortClf.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
            logger=logger,
        )
        self.exhaustive_effort_clf = with_implicit_async_voting(
            n_calls=cfg.ExhaustiveEffortClf.N_CALLS_FOR_VOTING,
            max_async_calls=cfg.ExhaustiveEffortClf.MAX_ASYNC_CALL_FOR_VOTING,
            vote_attr=BacktrackerSubAgentOutputFields.ANSWER,
            reason_attr=BacktrackerSubAgentOutputFields.RETROSPECTIVE,
            logger=logger,
        )(self.exhaustive_effort_clf)

        #####################################################
        ### Initialize most worthwhile pursuit classifier ###
        #####################################################

        self.most_worthwhile_pursuit_clf: InstructLmChatAgent[
            BacktrackerSubAgentLmResponseOutputData
        ] = InstructLmChatAgent(
            instruct_lm=cfg.MostWorthwhilePursuitClfCfg.INSTRUCT_LM,
            response_json_data_model=BacktrackerSubAgentLmResponseOutputData,
            max_tries_to_get_valid_response=cfg.MostWorthwhilePursuitClfCfg.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
            logger=logger,
        )
        self.most_worthwhile_pursuit_clf = with_implicit_async_voting(
            n_calls=cfg.MostWorthwhilePursuitClfCfg.N_CALLS_FOR_VOTING,
            max_async_calls=cfg.MostWorthwhilePursuitClfCfg.MAX_ASYNC_CALL_FOR_VOTING,
            vote_attr=BacktrackerSubAgentOutputFields.ANSWER,
            reason_attr=BacktrackerSubAgentOutputFields.RETROSPECTIVE,
            logger=logger,
        )(self.most_worthwhile_pursuit_clf)

        #############################################
        ### Initialize partial success classifier ###
        #############################################

        self.partial_success_clf: InstructLmChatAgent[
            BacktrackerSubAgentLmResponseOutputData
        ] = InstructLmChatAgent(
            instruct_lm=cfg.PartialSuccessClfCfg.INSTRUCT_LM,
            response_json_data_model=BacktrackerSubAgentLmResponseOutputData,
            max_tries_to_get_valid_response=cfg.PartialSuccessClfCfg.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
            logger=logger,
        )
        self.partial_success_clf = with_implicit_async_voting(
            n_calls=cfg.PartialSuccessClfCfg.N_CALLS_FOR_VOTING,
            max_async_calls=cfg.PartialSuccessClfCfg.MAX_ASYNC_CALL_FOR_VOTING,
            vote_attr=BacktrackerSubAgentOutputFields.ANSWER,
            reason_attr=BacktrackerSubAgentOutputFields.RETROSPECTIVE,
            logger=logger,
        )(self.partial_success_clf)

        ###################################################
        ### Initialize successful completion classifier ###
        ###################################################

        self.successful_completion_clf: InstructLmChatAgent[
            BacktrackerSubAgentLmResponseOutputData
        ] = InstructLmChatAgent(
            instruct_lm=cfg.SuccessfulCompletionClfCfg.INSTRUCT_LM,
            response_json_data_model=BacktrackerSubAgentLmResponseOutputData,
            max_tries_to_get_valid_response=cfg.SuccessfulCompletionClfCfg.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
            logger=logger,
        )
        self.successful_completion_clf = with_implicit_async_voting(
            n_calls=cfg.SuccessfulCompletionClfCfg.N_CALLS_FOR_VOTING,
            max_async_calls=cfg.SuccessfulCompletionClfCfg.MAX_ASYNC_CALL_FOR_VOTING,
            vote_attr=BacktrackerSubAgentOutputFields.ANSWER,
            reason_attr=BacktrackerSubAgentOutputFields.RETROSPECTIVE,
            logger=logger,
        )(self.successful_completion_clf)

    async def __call__(self, env_state: str) -> bool | None:
        """
        Invokes

        Returns:
            bool: Whether backtracking occured.
        """

        should_call_pre_lm_step_handler = self.pre_lm_step_handler is not None
        should_call_post_lm_step_approver = self.post_lm_step_approver is not None

        # Prepare prompt inputs (used by all sub-agents except most worthwhile pursuit clf)
        prompt_input_data = BacktrackerSubAgentPromptInputData(
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

        logger.info("Checking if the task has been successfully completed...")

        # Input messages for the LM
        input_messages = render_single_turn_prompt_templates_and_get_messages(
            user_message_input_data=prompt_input_data,
            user_prompt_template=SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY[
                cfg.SuccessfulCompletionClfCfg.PROMPTS_VERSION
            ].user_prompt_template,
            sys_message_input_data=None,  # TODO: Render dynamically, e.g., w/ RAG
            sys_prompt_template=SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY[
                cfg.SuccessfulCompletionClfCfg.PROMPTS_VERSION
            ].sys_prompt_template,
        )

        task_was_deemed_successfully_completed = False
        commit_olthad_update_fn: Callable | None = None
        while True:
            # Call pre-LM-step handler if needed
            if should_call_pre_lm_step_handler:
                emission = PreLmGenerationStepEmission(
                    agent_name=AgentName.SUCCESSFUL_COMPLETION_CLF,
                    cur_node_id=self.traversal._cur_node.id,
                    prompt_messages=input_messages,
                    n_streams_to_handle=cfg.SuccessfulCompletionClfCfg.N_CALLS_FOR_VOTING,
                )
                await call_or_await(self.pre_lm_step_handler, emission)

            # Invoke `self.successful_completion_clf` LM agent & parse answer choice
            return_obj = await self.successful_completion_clf(
                input_messages=input_messages,
                stream_handler=self.streams_handler,
            )
            lm_choice = extract_letter_from_multiple_choice_question_response(
                return_obj.output_data.answer,
                WAS_SUCCESSFULLY_COMPLETED_OPTIONS,
            )

            # Check if task was deemed successfully completed
            if lm_choice == WAS_SUCCESSFULLY_COMPLETED_OPTIONS[True].letter:
                task_was_deemed_successfully_completed = True
                # Acquire the appropriate pending update object from the traversal class
                pending_update = self.traversal.update_status_and_retrospective_of(
                    node=self.traversal.cur_node,
                    new_status=BacktrackedFromTaskStatus.SUCCESS,
                    new_retrospective=return_obj.output_data.retrospective,
                )
                commit_olthad_update_fn = pending_update.commit
                # Get the diff if we'll need it later to get approval
                if should_call_post_lm_step_approver:
                    diff = pending_update.get_diff()
            else:  # ...else, it was deemed not successfully completed
                if should_call_post_lm_step_approver:
                    # Get a diff w/ no changes to send for approval
                    diff = self.traversal.root_node.stringify(get_diff_lines=True)

            if should_call_post_lm_step_approver:
                # Call post-LM-step approver
                emission = PostLmGenerationStepEmission(
                    diff=diff, full_messages=return_obj.messages
                )
                lm_step_was_approved = await call_or_await(
                    self.post_lm_step_approver, emission=emission
                )
                if lm_step_was_approved:
                    break  # Break the while loop to go straight to the update
                else:
                    continue  # Loop (run the step) again
            else:  # There's no approver to call
                break

        if task_was_deemed_successfully_completed:
            # Commit the olthad update
            commit_olthad_update_fn()
            # Backtrack to the parent of the current node
            self.traversal.backtrack_to(self.traversal.cur_node.parent_id)
            # Return True to indicate that backtracking occured
            return True

        ##############################################################################
        ### LM STEP: Classify whether the task has been given an exhaustive effort ###
        ##############################################################################

        raise NotImplementedError

        # logger.info("Checking if an exhaustive effort was given...")

        # ...

        # if lm_choice == EFFORT_WAS_EXHAUSTIVE_OPTIONS[True].letter:

        #     ######################################################################
        #     ### LM STEP: Classify whether the completion was a partial success ###
        #     ######################################################################

        #     logger.info("Checking if task was partial succes (or failure)...")

        #     ...

        # else:  # Effort was not deemed exhaustive

        #     #######################################################################################
        #     ### LM STEP(S): Classify if ancestor tasks are (still) the most worthwhile pursuits ###
        #     #######################################################################################

        #     logger.info("Checking if ancestors are still worthwhile...")

        #     for (  # Iter through gradual reconstruction of olthad starting from cur=root
        #         root_node,
        #         cur_node,
        #     ) in input_data.root_task_node.iter_in_progress_descendants():

        #         ...

        #         if choice == IS_MOST_WORTHWHILE_OPTIONS[False].letter:
        #             # Backtrack to the this node

        #     # Finally, if ancestors are still deemed worthwhile, no backtracking warranted
