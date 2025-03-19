import inspect
from typing import Generator, Optional

from loguru import logger

from agent_framework.agents import SingleTurnChatAgent
from agent_framework.schema import Agent, LmStreamsHandler
from agent_framework.utils import with_implicit_async_voting
from sr_olthad.agents.backtracker.prompt import (
    EXHAUSTIVE_EFFORT_CLF_PROMPT_REGISTRY,
    MOST_WORTHWHILE_PURSUIT_CLF_PROMPT_REGISTRY,
    PARTIAL_SUCCESS_CLF_PROMPT_REGISTRY,
    SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY,
    WAS_SUCCESSFULLY_COMPLETED_OPTIONS,
    BacktrackerSubAgentLmResponseOutputData,
    BacktrackerSubAgentOutputFields,
    BacktrackerSubAgentPromptInputData,
)
from sr_olthad.config import BacktrackerCfg as cfg
from sr_olthad.emissions import (
    PostLmGenerationStepEmission,
    PostLmGenerationStepHandler,
    PreLmGenerationStepEmission,
    PreLmGenerationStepHandler,
)
from sr_olthad.olthad import BacktrackedFromTaskStatus, OlthadTraversal
from sr_olthad.schema import AgentName
from sr_olthad.utils import (
    extract_letter_from_multiple_choice_question_response,
)


class Backtracker(Agent):
    """
    The backtracker agent in the sr-OLTHAD system.
    """

    def __init__(
        self,
        olthad_traversal: OlthadTraversal,
        pre_lm_generation_step_handler: Optional[
            PreLmGenerationStepHandler
        ] = None,
        post_lm_generation_step_handler: Optional[
            PostLmGenerationStepHandler
        ] = None,
        streams_handler: Optional[LmStreamsHandler] = None,
    ):
        """
        Initializes the backtracker agent.

        Args:
            streams_handler (Optional[LmStreamsHandler], optional): The handler to use for
                handling potentially multiple LM response streams. Defaults to None.
            callback_after_each_lm_step (Optional[Callable[[List[InstructLmMessage]], None]], optional):
                A function to call after each language model step. Defaults to None.
        """
        self.traversal = olthad_traversal
        self.streams_handler = streams_handler
        self.pre_lm_generation_step_handler = pre_lm_generation_step_handler
        self.post_lm_step_handler = post_lm_generation_step_handler

        ###############################################
        ### Initialize exhaustive effort classifier ###
        ###############################################

        exhaustive_effort_prompts = EXHAUSTIVE_EFFORT_CLF_PROMPT_REGISTRY[
            cfg.ExhaustiveEffortClf.PROMPTS_VERSION
        ]
        self.exhaustive_effort_clf: SingleTurnChatAgent[
            BacktrackerSubAgentLmResponseOutputData
        ] = SingleTurnChatAgent(
            instruct_lm=cfg.ExhaustiveEffortClf.INSTRUCT_LM,
            response_json_data_model=BacktrackerSubAgentLmResponseOutputData,
            # TODO: Render sys prompt dynamically, e.g., w/ RAG of relevant good examples
            sys_prompt=exhaustive_effort_prompts.sys_prompt_template.render(),
            user_prompt_template=exhaustive_effort_prompts.user_prompt_template,
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

        most_worthwhile_pursuit_prompts = (
            MOST_WORTHWHILE_PURSUIT_CLF_PROMPT_REGISTRY[
                cfg.MostWorthwhilePursuitClfCfg.PROMPTS_VERSION
            ]
        )
        self.most_worthwhile_pursuit_clf: SingleTurnChatAgent[
            BacktrackerSubAgentLmResponseOutputData
        ] = SingleTurnChatAgent(
            instruct_lm=cfg.MostWorthwhilePursuitClfCfg.INSTRUCT_LM,
            response_json_data_model=BacktrackerSubAgentLmResponseOutputData,
            # TODO: Render sys prompt dynamically, e.g., w/ RAG of relevant good examples
            sys_prompt=most_worthwhile_pursuit_prompts.sys_prompt_template.render(),
            user_prompt_template=most_worthwhile_pursuit_prompts.user_prompt_template,
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

        partial_success_prompts = PARTIAL_SUCCESS_CLF_PROMPT_REGISTRY[
            cfg.PartialSuccessClfCfg.PROMPTS_VERSION
        ]
        self.partial_success_clf: SingleTurnChatAgent[
            BacktrackerSubAgentLmResponseOutputData
        ] = SingleTurnChatAgent(
            instruct_lm=cfg.PartialSuccessClfCfg.INSTRUCT_LM,
            response_json_data_model=BacktrackerSubAgentLmResponseOutputData,
            # TODO: Render sys prompt dynamically, e.g., w/ RAG of relevant good examples
            sys_prompt=partial_success_prompts.sys_prompt_template.render(),
            user_prompt_template=partial_success_prompts.user_prompt_template,
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

        successful_completion_prompts = (
            SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY[
                cfg.SuccessfulCompletionClfCfg.PROMPTS_VERSION
            ]
        )
        self.successful_completion_clf: SingleTurnChatAgent[
            BacktrackerSubAgentLmResponseOutputData
        ] = SingleTurnChatAgent(
            instruct_lm=cfg.SuccessfulCompletionClfCfg.INSTRUCT_LM,
            response_json_data_model=BacktrackerSubAgentLmResponseOutputData,
            # TODO: Render sys prompt dynamically, e.g., w/ RAG of relevant good examples
            sys_prompt=successful_completion_prompts.sys_prompt_template.render(),
            user_prompt_template=successful_completion_prompts.user_prompt_template,
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

    async def __call__(self, env_state: str) -> None:

        sub_agent_input_data = BacktrackerSubAgentPromptInputData(
            env_state=env_state,
            olthad=self.traversal.root_node.stringify(  # Pre-stringify w/ args
                redact_planned_subtasks_below=self.traversal.cur_node.id,
                obfuscate_status_of=self.traversal.cur_node.id,
            ),
            task_in_question=self.traversal.cur_node.stringify(
                redact_planned_subtasks_below=self.traversal.cur_node.id,
                obfuscate_status_of=self.traversal.cur_node.id,
            ),
        )

        #################################################################
        ### Classify whether the task has been successfully completed ###
        #################################################################

        logger.info("Checking if the task has been successfully completed...")

        # Pre-LM-generation step handler
        if self.pre_lm_generation_step_handler is not None:
            in_messages = self.successful_completion_clf.prepare_input_messages(
                input_data=sub_agent_input_data
            )  # TODO: Redundant call... rethink design bc of this? (see README)
            emission = PreLmGenerationStepEmission(
                agent_name=AgentName.SUCCESSFUL_COMPLETION_CLF,
                prompt_messages=in_messages,
                n_streams_to_handle=cfg.SuccessfulCompletionClfCfg.N_CALLS_FOR_VOTING,
            )
            if inspect.iscoroutinefunction(
                self.pre_lm_generation_step_handler
            ):
                await self.pre_lm_generation_step_handler(emission)
            else:
                self.pre_lm_generation_step_handler(emission)

        step_is_approved = False
        while not step_is_approved:
            # Invoke `self.successful_completion_clf`
            return_obj = await self.successful_completion_clf(
                prompt_template_data=sub_agent_input_data,
                stream_handler=self.streams_handler,
            )

            choice = extract_letter_from_multiple_choice_question_response(
                return_obj.output_data.answer,
                WAS_SUCCESSFULLY_COMPLETED_OPTIONS,
            )

            if self.post_lm_step_handler is None:
                break
            # Otherwise, call the post-LM-generation step handler to get approval...

            # Prepare emission data
            full_messages = return_obj.messages
            cur_parent_id = self.traversal.cur_node.parent_id
            make_update_after_approval = None
            if cur_parent_id is None:  # Root node
                if choice == WAS_SUCCESSFULLY_COMPLETED_OPTIONS[True].letter:
                    status = BacktrackedFromTaskStatus.SUCCESS
                    retrospective = return_obj.output_data.retrospective
                    make_update_after_approval = self.traversal.update_status_and_retrospective_of_rood_node(
                        new_status=status,
                        new_retrospective=retrospective,
                        should_yield_diff_and_receive_approval_before_update=True,
                    )
                    difflines = next(make_update_after_approval)
                else:
                    difflines = self.traversal.cur_node.stringify(
                        get_diff_lines=True,
                    )
            else:
                if choice == WAS_SUCCESSFULLY_COMPLETED_OPTIONS[True].letter:
                    cur_parent = self.traversal.nodes[cur_parent_id]
                    status = BacktrackedFromTaskStatus.SUCCESS
                    retrospective = return_obj.output_data.retrospective
                    make_update_after_approval = cur_parent.update_status_and_retrospective_of_in_progress_subtask(
                        status_to_assign=status,
                        retrospective_to_assign=retrospective,
                        should_yield_diff_and_receive_approval_before_update=True,
                        diff_root_node=self.traversal.root_node,
                    )
                    difflines = next(make_update_after_approval)
                else:
                    difflines = self.traversal.cur_node.stringify(
                        get_diff_lines=True,
                    )

            # Send emission to post-LM-generation step handler
            emission = PostLmGenerationStepEmission(
                diff_lines=difflines,
                full_messages=full_messages,
            )
            if inspect.iscoroutinefunction(self.post_lm_step_handler):
                step_is_approved = await self.post_lm_step_handler(emission)
            else:
                step_is_approved = self.post_lm_step_handler(emission)

            # Send approval back to generator so it knows to make update
            if make_update_after_approval is not None:
                make_update_after_approval: Generator  # Make mypy happy
                make_update_after_approval.send(step_is_approved)

        raise NotImplementedError

        # #####################################################################
        # ### Classify whether the task has been given an exhaustive effort ###
        # #####################################################################

        # logger.info("Checking if an exhaustive effort was given...")

        # return_obj = await self.exhaustive_effort_clf(
        #     prompt_template_data=sub_agent_input_data,
        #     stream_handler=self.streams_handler,
        # )

        # if self.callback_after_each_lm_step is not None:
        #     self.callback_after_each_lm_step(return_obj.messages)

        # choice = extract_letter_from_multiple_choice_question_response(
        #     return_obj.output_data.answer, EFFORT_WAS_EXHAUSTIVE_OPTIONS
        # )

        # if choice == EFFORT_WAS_EXHAUSTIVE_OPTIONS[True].letter:

        #     #############################################################
        #     ### Classify whether the completion was a partial success ###
        #     #############################################################

        #     logger.info("Checking if task was partial succes (or failure)...")

        #     return_obj = await self.partial_success_clf(
        #         prompt_template_data=sub_agent_input_data,
        #         stream_handler=self.streams_handler,
        #     )

        #     if self.callback_after_each_lm_step is not None:
        #         self.callback_after_each_lm_step(return_obj.messages)

        #     choice = extract_letter_from_multiple_choice_question_response(
        #         return_obj.output_data.answer, WAS_PARTIAL_SUCCESS_OPTIONS
        #     )

        #     if choice == WAS_PARTIAL_SUCCESS_OPTIONS[True].letter:
        #         return BacktrackerReturn(
        #             output_data=BacktrackerOutputData(
        #                 backtracked_from_status_to_assign=BacktrackedFromTaskStatus.PARTIAL_SUCCESS,
        #                 retrospective_to_assign=return_obj.output_data.retrospective,
        #                 id_of_ancestor_to_backtrack_to=input_data.current_task_node.parent_id,
        #             )
        #         )
        #     else:
        #         return BacktrackerReturn(
        #             output_data=BacktrackerOutputData(
        #                 backtracked_from_status_to_assign=BacktrackedFromTaskStatus.FAILURE,
        #                 retrospective_to_assign=return_obj.output_data.retrospective,
        #                 id_of_ancestor_to_backtrack_to=input_data.current_task_node.parent_id,
        #             )
        #         )

        # else:  # Effort was not deemed exhaustive

        #     ###########################################################################
        #     ### Classify if ancestor tasks are (still) the most worthwhile pursuits ###
        #     ###########################################################################

        #     logger.info("Checking if ancestors are still worthwhile...")

        #     for (  # Iter through gradual reconstruction of olthad starting from cur=root
        #         root_node,
        #         cur_node,
        #     ) in input_data.root_task_node.iter_in_progress_descendants():

        #         sub_agent_input_data = BacktrackerSubAgentPromptInputData(
        #             env_state=input_data.env_state,
        #             olthad=root_node.stringify(
        #                 redact_planned_subtasks_below=cur_node.id,
        #                 obfuscate_status_of=cur_node.id,
        #             ),
        #             task_in_question=cur_node.stringify(
        #                 redact_planned_subtasks_below=cur_node.id,
        #                 obfuscate_status_of=cur_node.id,
        #             ),
        #         )

        #         return_obj = await self.most_worthwhile_pursuit_clf(
        #             prompt_template_data=sub_agent_input_data,
        #             stream_handler=self.streams_handler,
        #         )

        #         if self.callback_after_each_lm_step is not None:
        #             self.callback_after_each_lm_step(return_obj.messages)

        #         choice = extract_letter_from_multiple_choice_question_response(
        #             return_obj.output_data.answer, IS_MOST_WORTHWHILE_OPTIONS
        #         )

        #         if choice == IS_MOST_WORTHWHILE_OPTIONS[False].letter:
        #             return BacktrackerReturn(
        #                 output_data=BacktrackerOutputData(
        #                     backtracked_from_status_to_assign=BacktrackedFromTaskStatus.DROPPED,
        #                     retrospective_to_assign=return_obj.output_data.retrospective,
        #                     id_of_ancestor_to_backtrack_to=cur_node.parent_id,
        #                 )
        #             )

        #     # Finally, if ancestors are still deemed worthwhile, no backtracking warranted
        #     return BacktrackerReturn(
        #         output_data=BacktrackerOutputData(
        #             backtracked_from_status_to_assign=None,
        #             retrospective_to_assign=None,
        #             id_of_ancestor_to_backtrack_to=None,
        #         )
        #     )
