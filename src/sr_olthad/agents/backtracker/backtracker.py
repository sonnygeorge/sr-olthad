from dataclasses import dataclass
from typing import Callable, List, Optional

from loguru import logger
from pydantic import BaseModel

from agent_framework.agents import SingleTurnChatAgent
from agent_framework.schema import Agent, InstructLmMessage, LmStreamHandler
from agent_framework.utils import with_implicit_async_voting
from sr_olthad.agents.backtracker.prompt import (
    EFFORT_WAS_EXHAUSTIVE_OPTIONS,
    EXHAUSTIVE_EFFORT_CLF_PROMPT_REGISTRY,
    IS_MOST_WORTHWHILE_OPTIONS,
    MOST_WORTHWHILE_PURSUIT_CLF_PROMPT_REGISTRY,
    PARTIAL_SUCCESS_CLF_PROMPT_REGISTRY,
    SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY,
    WAS_PARTIAL_SUCCESS_OPTIONS,
    WAS_SUCCESSFULLY_COMPLETED_OPTIONS,
    BacktrackerSubAgentLmResponseOutputData,
    BacktrackerSubAgentOutputFields,
    BacktrackerSubAgentPromptInputData,
)
from sr_olthad.config import BacktrackerCfg as cfg
from sr_olthad.task_node import BacktrackedFromTaskStatus, TaskNode, TaskStatus
from sr_olthad.utils import (
    extract_letter_from_multiple_choice_question_response,
)


class BacktrackerInputData(BaseModel):
    """
    Input data for the Backtracker agent.

    Attributes:
        env_state (str): PRE-STRINGIFIED current environment state.
        root_task_node (TaskNode): The root task node of the OLTHAD.
        current_task_node (TaskNode): The task node we're considering backtracking from.
    """

    env_state: str
    root_task_node: TaskNode
    current_task_node: TaskNode


class BacktrackerOutputData(BaseModel):
    """
    Output data for the Backtracker agent.

    Attributes:
        status_to_assign (Optional[BacktrackedFromTaskStatus]): If backtracking is deemed
            warranted, this is the status to assign to the task in question. Else, `None`.
        retrospective_to_assign (Optional[str | List[str]]): If backtracking is deemed
            warranted, this is the retrospective to assign to the task in question. Else,
            `None`.
        id_of_ancestor_to_backtrack_to (Optional[TaskNode]]):
            If backtracking is deeed warranted, this is the id of the ancestor node to
            backtrack to Else, `None`.
    """

    backtracked_from_status_to_assign: Optional[BacktrackedFromTaskStatus]
    retrospective_to_assign: Optional[str | List[str]]
    id_of_ancestor_to_backtrack_to: Optional[TaskNode]


@dataclass
class BacktrackerReturn:
    output_data: BacktrackerOutputData


class Backtracker(Agent):
    """
    The backtracker agent in the sr-OLTHAD system.
    """

    def __init__(
        self,
        stream_handler: Optional[LmStreamHandler] = None,
        callback_after_each_lm_step: Optional[
            Callable[[List[InstructLmMessage]], None]
        ] = None,
    ):
        """
        Initializes the backtracker agent.

        Args:
            stream_handler (Optional[LmStreamHandler], optional): The handler to use for
                streaming language model responses. Defaults to None.
            callback_after_each_lm_step (Optional[Callable[[List[InstructLmMessage]], None]], optional):
                A function to call after each language model step. Defaults to None.
        """
        self.stream_handler = stream_handler
        self.callback_after_each_lm_step = callback_after_each_lm_step

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

    async def __call__(
        self,
        input_data: BacktrackerInputData,
    ) -> BacktrackerReturn:
        """
        Run the backtracker agent.

        Args:
            input_data (BacktrackerInputData): The input data.

        Returns:
            BacktrackerReturn: The output return object with an `output_data` attribute
                of type `BacktrackerOutputData`.
        """

        sub_agent_input_data = BacktrackerSubAgentPromptInputData(
            env_state=input_data.env_state,
            olthad=input_data.root_task_node.stringify(  # Pre-stringify w/ args
                redact_planned_subtasks_below=input_data.current_task_node.id,
                obfuscate_status_of=input_data.current_task_node.id,
            ),
            task_in_question=input_data.current_task_node.stringify(
                redact_planned_subtasks_below=input_data.current_task_node.id,
                obfuscate_status_of=input_data.current_task_node.id,
            ),
        )

        #################################################################
        ### Classify whether the task has been successfully completed ###
        #################################################################

        logger.info("Checking if the task has been successfully completed...")

        return_obj = await self.successful_completion_clf(
            prompt_template_data=sub_agent_input_data,
            stream_handler=self.stream_handler,
        )

        if self.callback_after_each_lm_step is not None:
            self.callback_after_each_lm_step(return_obj.messages)

        choice = extract_letter_from_multiple_choice_question_response(
            return_obj.output_data.answer, WAS_SUCCESSFULLY_COMPLETED_OPTIONS
        )

        if choice == WAS_SUCCESSFULLY_COMPLETED_OPTIONS[True].letter:
            input_data.current_task_node.status = TaskStatus.SUCCESS
            return BacktrackerReturn(
                output_data=BacktrackerOutputData(
                    backtracked_from_status_to_assign=BacktrackedFromTaskStatus.SUCCESS,
                    retrospective_to_assign=return_obj.output_data.retrospective,
                    id_of_ancestor_to_backtrack_to=input_data.current_task_node.parent_id,
                )
            )

        #####################################################################
        ### Classify whether the task has been given an exhaustive effort ###
        #####################################################################

        logger.info("Checking if an exhaustive effort was given...")

        return_obj = await self.exhaustive_effort_clf(
            prompt_template_data=sub_agent_input_data,
            stream_handler=self.stream_handler,
        )

        if self.callback_after_each_lm_step is not None:
            self.callback_after_each_lm_step(return_obj.messages)

        choice = extract_letter_from_multiple_choice_question_response(
            return_obj.output_data.answer, EFFORT_WAS_EXHAUSTIVE_OPTIONS
        )

        if choice == EFFORT_WAS_EXHAUSTIVE_OPTIONS[True].letter:

            #############################################################
            ### Classify whether the completion was a partial success ###
            #############################################################

            logger.info("Checking if task was partial succes (or failure)...")

            return_obj = await self.partial_success_clf(
                prompt_template_data=sub_agent_input_data,
                stream_handler=self.stream_handler,
            )

            if self.callback_after_each_lm_step is not None:
                self.callback_after_each_lm_step(return_obj.messages)

            choice = extract_letter_from_multiple_choice_question_response(
                return_obj.output_data.answer, WAS_PARTIAL_SUCCESS_OPTIONS
            )

            if choice == WAS_PARTIAL_SUCCESS_OPTIONS[True].letter:
                return BacktrackerReturn(
                    output_data=BacktrackerOutputData(
                        backtracked_from_status_to_assign=BacktrackedFromTaskStatus.PARTIAL_SUCCESS,
                        retrospective_to_assign=return_obj.output_data.retrospective,
                        id_of_ancestor_to_backtrack_to=input_data.current_task_node.parent_id,
                    )
                )
            else:
                return BacktrackerReturn(
                    output_data=BacktrackerOutputData(
                        backtracked_from_status_to_assign=BacktrackedFromTaskStatus.FAILURE,
                        retrospective_to_assign=return_obj.output_data.retrospective,
                        id_of_ancestor_to_backtrack_to=input_data.current_task_node.parent_id,
                    )
                )

        else:  # Effort was not deemed exhaustive

            ###########################################################################
            ### Classify if ancestor tasks are (still) the most worthwhile pursuits ###
            ###########################################################################

            logger.info("Checking if ancestors are still worthwhile...")

            for (  # Iter through gradual reconstruction of olthad starting from cur=root
                root_node,
                cur_node,
            ) in input_data.root_task_node.iter_in_progress_descendants():

                sub_agent_input_data = BacktrackerSubAgentPromptInputData(
                    env_state=input_data.env_state,
                    olthad=root_node.stringify(
                        redact_planned_subtasks_below=cur_node.id,
                        obfuscate_status_of=cur_node.id,
                    ),
                    task_in_question=cur_node.stringify(
                        redact_planned_subtasks_below=cur_node.id,
                        obfuscate_status_of=cur_node.id,
                    ),
                )

                return_obj = await self.most_worthwhile_pursuit_clf(
                    prompt_template_data=sub_agent_input_data,
                    stream_handler=self.stream_handler,
                )

                if self.callback_after_each_lm_step is not None:
                    self.callback_after_each_lm_step(return_obj.messages)

                choice = extract_letter_from_multiple_choice_question_response(
                    return_obj.output_data.answer, IS_MOST_WORTHWHILE_OPTIONS
                )

                if choice == IS_MOST_WORTHWHILE_OPTIONS[False].letter:
                    return BacktrackerReturn(
                        output_data=BacktrackerOutputData(
                            backtracked_from_status_to_assign=BacktrackedFromTaskStatus.DROPPED,
                            retrospective_to_assign=return_obj.output_data.retrospective,
                            id_of_ancestor_to_backtrack_to=cur_node.parent_id,
                        )
                    )

            # Finally, if ancestors are still deemed worthwhile, no backtracking warranted
            return BacktrackerReturn(
                output_data=BacktrackerOutputData(
                    backtracked_from_status_to_assign=None,
                    retrospective_to_assign=None,
                    id_of_ancestor_to_backtrack_to=None,
                )
            )
