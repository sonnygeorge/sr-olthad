from dataclasses import dataclass
from typing import Callable, List, Optional

from loguru import logger
from pydantic import BaseModel

from agent_framework.agents import SingleTurnChatAgent
from agent_framework.schema import Agent, InstructLmMessages, LmStreamHandler
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
    BacktrackerSubAgentInputPromptData,
    BacktrackerSubAgentOutputFields,
    BacktrackerSubAgentOutputPromptData,
)
from sr_olthad.config import BacktrackerCfg as cfg
from sr_olthad.olthad import BacktrackedFromTaskStatus, TaskNode, TaskStatus
from sr_olthad.utils import (
    extract_letter_from_multiple_choice_question_response,
)


class BacktrackerInputData(BaseModel):
    """
    Input data for the backtracker agent.

    Attributes:
        env_state (str): STRINGIFIED current environment state.
        olthad_root (TaskNode): The root node of the OLTHAD being traversed.
        task_in_question (TaskNode): The node we're considering backtracking from.
    """

    env_state: str
    olthad_root: TaskNode
    task_in_question: TaskNode


class BacktrackerOutputData(BaseModel):
    status_to_assign: BacktrackedFromTaskStatus
    retrospective: Optional[str | List[str]]
    ancestor_to_backtrack_to_if_not_parent: Optional[
        TaskNode | List[TaskNode]
    ] = None


@dataclass
class BacktrackerReturn:
    output_data: BacktrackerOutputData


class Backtracker(Agent):
    def __init__(self):
        ###############################################
        ### Initialize exhaustive effort classifier ###
        ###############################################

        exhaustive_effort_prompts = EXHAUSTIVE_EFFORT_CLF_PROMPT_REGISTRY[
            cfg.ExhaustiveEffortClf.PROMPTS_VERSION
        ]
        self.exhaustive_effort_clf: SingleTurnChatAgent[
            BacktrackerSubAgentOutputPromptData
        ] = SingleTurnChatAgent(
            instruct_lm=cfg.ExhaustiveEffortClf.INSTRUCT_LM,
            response_json_data_model=BacktrackerSubAgentOutputPromptData,
            # TODO: Render sys prompt dynamically, e.g., w/ RAG of relevant good examples
            sys_prompt=exhaustive_effort_prompts.sys_prompt_template.render(),
            user_prompt_template=exhaustive_effort_prompts.user_prompt_template,
            max_tries_to_get_valid_response=cfg.ExhaustiveEffortClf.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
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
            BacktrackerSubAgentOutputPromptData
        ] = SingleTurnChatAgent(
            instruct_lm=cfg.MostWorthwhilePursuitClfCfg.INSTRUCT_LM,
            response_json_data_model=BacktrackerSubAgentOutputPromptData,
            # TODO: Render sys prompt dynamically, e.g., w/ RAG of relevant good examples
            sys_prompt=most_worthwhile_pursuit_prompts.sys_prompt_template.render(),
            user_prompt_template=most_worthwhile_pursuit_prompts.user_prompt_template,
            max_tries_to_get_valid_response=cfg.MostWorthwhilePursuitClfCfg.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
        )
        self.most_worthwhile_pursuit_clf = with_implicit_async_voting(
            n_calls=cfg.MostWorthwhilePursuitClfCfg.N_CALLS_FOR_VOTING,
            max_async_calls=cfg.MostWorthwhilePursuitClfCfg.MAX_ASYNC_CALL_FOR_VOTING,
            vote_attr=BacktrackerSubAgentOutputFields.ANSWER,
            reason_attr=BacktrackerSubAgentOutputFields.RETROSPECTIVE,
            logger=logger,
        )(self.most_worthwhile_pursuit_clf)

        ###########################################
        ### Initialize partial success classifier ###
        ###########################################

        partial_success_prompts = PARTIAL_SUCCESS_CLF_PROMPT_REGISTRY[
            cfg.PartialSuccessClfCfg.PROMPTS_VERSION
        ]
        self.partial_success_clf: SingleTurnChatAgent[
            BacktrackerSubAgentOutputPromptData
        ] = SingleTurnChatAgent(
            instruct_lm=cfg.PartialSuccessClfCfg.INSTRUCT_LM,
            response_json_data_model=BacktrackerSubAgentOutputPromptData,
            # TODO: Render sys prompt dynamically, e.g., w/ RAG of relevant good examples
            sys_prompt=partial_success_prompts.sys_prompt_template.render(),
            user_prompt_template=partial_success_prompts.user_prompt_template,
            max_tries_to_get_valid_response=cfg.PartialSuccessClfCfg.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
        )
        self.partial_success_clf = with_implicit_async_voting(
            n_calls=cfg.PartialSuccessClfCfg.N_CALLS_FOR_VOTING,
            max_async_calls=cfg.PartialSuccessClfCfg.MAX_ASYNC_CALL_FOR_VOTING,
            vote_attr=BacktrackerSubAgentOutputFields.ANSWER,
            reason_attr=BacktrackerSubAgentOutputFields.RETROSPECTIVE,
            logger=logger,
        )(self.partial_success_clf)

        ########################################################
        ### Initialize successful completion classifier ###
        ########################################################

        successful_completion_prompts = (
            SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY[
                cfg.SuccessfulCompletionClfCfg.PROMPTS_VERSION
            ]
        )
        self.successful_completion_clf: SingleTurnChatAgent[
            BacktrackerSubAgentOutputPromptData
        ] = SingleTurnChatAgent(
            instruct_lm=cfg.SuccessfulCompletionClfCfg.INSTRUCT_LM,
            response_json_data_model=BacktrackerSubAgentOutputPromptData,
            # TODO: Render sys prompt dynamically, e.g., w/ RAG of relevant good examples
            sys_prompt=successful_completion_prompts.sys_prompt_template.render(),
            user_prompt_template=successful_completion_prompts.user_prompt_template,
            max_tries_to_get_valid_response=cfg.SuccessfulCompletionClfCfg.MAX_TRIES_TO_GET_VALID_LM_RESPONSE,
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
        stream_handler: Optional[LmStreamHandler] = None,
        callback_after_each_lm_step: Optional[
            Callable[[List[InstructLmMessages]], None]
        ] = None,
    ) -> BacktrackerReturn:
        """
        Run the backtracker agent."

        Args:
            input_data (BacktrackerInputData): The input data for the agent.
            ...
        """

        sub_agent_input_data = BacktrackerSubAgentInputPromptData(
            env_state=input_data.env_state,
            olthad=input_data.olthad_root.stringify(  # Pre-stringify w/ args
                redact_planned_subtasks_below=input_data.task_in_question.task,
                obfuscate_status_of=input_data.task_in_question.task,
            ),
            task_in_question=input_data.task_in_question.stringify(
                redact_planned_subtasks_below=input_data.task_in_question.task,
                obfuscate_status_of=input_data.task_in_question.task,
            ),
        )

        #################################################################
        ### Classify whether the task has been successfully completed ###
        #################################################################

        logger.info("Checking if the task has been successfully completed...")

        return_obj = await self.successful_completion_clf(
            prompt_template_data=sub_agent_input_data,
            stream_handler=stream_handler,
        )

        callback_after_each_lm_step(return_obj.messages)

        choice = extract_letter_from_multiple_choice_question_response(
            return_obj.output_data.answer, WAS_SUCCESSFULLY_COMPLETED_OPTIONS
        )

        if choice == WAS_SUCCESSFULLY_COMPLETED_OPTIONS[True].letter:
            input_data.task_in_question.status = TaskStatus.SUCCESS
            return BacktrackerReturn(
                output_data=BacktrackerOutputData(
                    status_to_assign=BacktrackedFromTaskStatus.SUCCESS,
                    retrospective=return_obj.output_data.retrospective,
                )
            )

        #####################################################################
        ### Classify whether the task has been given an exhaustive effort ###
        #####################################################################

        logger.info("Checking if an exhaustive effort was given...")

        return_obj = await self.exhaustive_effort_clf(
            prompt_template_data=sub_agent_input_data,
            stream_handler=stream_handler,
        )
        callback_after_each_lm_step(return_obj.messages)

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
                stream_handler=stream_handler,
            )

            callback_after_each_lm_step(return_obj.messages)

            choice = extract_letter_from_multiple_choice_question_response(
                return_obj.output_data.answer, WAS_PARTIAL_SUCCESS_OPTIONS
            )

            if choice == WAS_PARTIAL_SUCCESS_OPTIONS[True].letter:
                return BacktrackerReturn(
                    output_data=BacktrackerOutputData(
                        status_to_assign=BacktrackedFromTaskStatus.PARTIAL_SUCCESS,
                        retrospective=return_obj.output_data.retrospective,
                    )
                )
            else:
                return BacktrackerReturn(
                    output_data=BacktrackerOutputData(
                        status_to_assign=BacktrackedFromTaskStatus.FAILURE,
                        retrospective=return_obj.output_data.retrospective,
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
            ) in input_data.olthad_root.iter_in_progress_descendants():

                sub_agent_input_data = BacktrackerSubAgentInputPromptData(
                    env_state=input_data.env_state,
                    olthad=root_node.stringify(
                        redact_planned_subtasks_below=cur_node.task,
                        obfuscate_status_of=cur_node.task,
                    ),
                    task_in_question=cur_node.stringify(
                        redact_planned_subtasks_below=cur_node.task,
                        obfuscate_status_of=cur_node.task,
                    ),
                )

                return_obj = await self.most_worthwhile_pursuit_clf(
                    prompt_template_data=sub_agent_input_data,
                    stream_handler=stream_handler,
                )

                callback_after_each_lm_step(return_obj.messages)

                choice = extract_letter_from_multiple_choice_question_response(
                    return_obj.output_data.answer, IS_MOST_WORTHWHILE_OPTIONS
                )

                if choice == IS_MOST_WORTHWHILE_OPTIONS[False].letter:
                    return BacktrackerReturn(
                        output_data=BacktrackerOutputData(
                            status_to_assign=BacktrackedFromTaskStatus.DROPPED,
                            retrospective=return_obj.output_data.retrospective,
                            ancestor_to_backtrack_to_if_not_parent=cur_node,
                        )
                    )

            # Finally, if no ancestors are worth dropping, status stays in progress
            return BacktrackerReturn(
                output_data=BacktrackerOutputData(
                    status_to_assign=BacktrackedFromTaskStatus.IN_PROGRESS,
                    retrospective=None,
                )
            )
