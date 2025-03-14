from loguru import logger
from pydantic import BaseModel
from typing import Optional, Callable, List

from enums import BinaryCaseStr
from schema import Agent, AgentReturn, LmStreamHandler, InstructLmMessage
from agents import SingleTurnChatMultipleChoiceAgent
from sr_olthad.agents.config import BacktrackerConfig as cfg
from sr_olthad.agents.backtracker.prompts import (
    WAS_SUCCESSFULLY_COMPLETED_OPTIONS,
    IS_MOST_WORTHWHILE_OPTIONS,
    EFFORT_WAS_EXHAUSTIVE_OPTIONS,
    WAS_PARTIAL_SUCCESS_OPTIONS,
)
from sr_olthad.enums import BacktrackedFromTaskStatus, TaskStatus
from sr_olthad.olthad.task_node import TaskNode
from utils import extract_letter_choice_from_text


class BacktrackerSubAgentInputData(BaseModel):
    env_state: str
    olthad: str  # (pre-stringified)
    task_in_question: str  # (pre-stringified)


class BacktrackerInputData(BaseModel):
    env_state: str
    olthad: TaskNode  # The root node w/ all the descendants
    task_in_question: TaskNode  # The node we're considering backtracking from


class BacktrackerOutputData(BaseModel):
    chosen_status: BacktrackedFromTaskStatus
    retrospective: Optional[str]
    backtrack_to: Optional[TaskNode]


class BacktrackerReturn(AgentReturn):
    output_data: BacktrackerOutputData


class Backtracker(Agent):
    def __init__(self):
        # Initialize exhaustive effort classifier
        self.exhaustive_effort_clf: SingleTurnChatMultipleChoiceAgent[
            BacktrackerInputData
        ] = SingleTurnChatMultipleChoiceAgent(
            instruct_lm=cfg.ExhaustiveEffortClfConfig.INSTRUCT_LM,
            multiple_choice_options=EFFORT_WAS_EXHAUSTIVE_OPTIONS,
            sys_prompt=cfg.ExhaustiveEffortClfConfig.SYS_PROMPT,
            user_prompt_template=cfg.ExhaustiveEffortClfConfig.USER_PROMPT_TEMPLATE,
            n_implicit_calls_for_voting=cfg.ExhaustiveEffortClfConfig.N_CALLS_FOR_VOTING,
            max_implicit_async_calls_for_voting=cfg.ExhaustiveEffortClfConfig.MAX_ASYNC_CALL_FOR_VOTING,
            input_data_model=BacktrackerSubAgentInputData,
            max_tries_to_get_valid_response=cfg.ExhaustiveEffortClfConfig.MAX_TRIES_TO_GET_VALID_RESPONSE,
            logger=logger,
        )
        # Initialize most worthwhile pursuit classifier
        self.most_worthwhile_pursuit_clf: SingleTurnChatMultipleChoiceAgent[
            BacktrackerInputData
        ] = SingleTurnChatMultipleChoiceAgent(
            instruct_lm=cfg.MostWorthwhilePursuitClfConfig.INSTRUCT_LM,
            multiple_choice_options=IS_MOST_WORTHWHILE_OPTIONS,
            sys_prompt=cfg.MostWorthwhilePursuitClfConfig.SYS_PROMPT,
            user_prompt_template=cfg.MostWorthwhilePursuitClfConfig.USER_PROMPT_TEMPLATE,
            n_implicit_calls_for_voting=cfg.MostWorthwhilePursuitClfConfig.N_CALLS_FOR_VOTING,
            max_implicit_async_calls_for_voting=cfg.MostWorthwhilePursuitClfConfig.MAX_ASYNC_CALL_FOR_VOTING,
            input_data_model=BacktrackerSubAgentInputData,
            max_tries_to_get_valid_response=cfg.MostWorthwhilePursuitClfConfig.MAX_TRIES_TO_GET_VALID_RESPONSE,
            logger=logger,
        )
        # Initialize partial success classifier
        self.partial_success_clf: SingleTurnChatMultipleChoiceAgent[
            BacktrackerInputData
        ] = SingleTurnChatMultipleChoiceAgent(
            instruct_lm=cfg.PartialSuccessClfConfig.INSTRUCT_LM,
            multiple_choice_options=WAS_PARTIAL_SUCCESS_OPTIONS,
            sys_prompt=cfg.PartialSuccessClfConfig.SYS_PROMPT,
            user_prompt_template=cfg.PartialSuccessClfConfig.USER_PROMPT_TEMPLATE,
            n_implicit_calls_for_voting=cfg.PartialSuccessClfConfig.N_CALLS_FOR_VOTING,
            max_implicit_async_calls_for_voting=cfg.PartialSuccessClfConfig.MAX_ASYNC_CALL_FOR_VOTING,
            input_data_model=BacktrackerSubAgentInputData,
            max_tries_to_get_valid_response=cfg.PartialSuccessClfConfig.MAX_TRIES_TO_GET_VALID_RESPONSE,
            logger=logger,
        )
        # Initialize successful completion classifier
        self.successful_completion_clf: SingleTurnChatMultipleChoiceAgent[
            BacktrackerInputData
        ] = SingleTurnChatMultipleChoiceAgent(
            instruct_lm=cfg.SuccessfulCompletionClfConfig.INSTRUCT_LM,
            multiple_choice_options=WAS_SUCCESSFULLY_COMPLETED_OPTIONS,
            sys_prompt=cfg.SuccessfulCompletionClfConfig.SYS_PROMPT,
            user_prompt_template=cfg.SuccessfulCompletionClfConfig.USER_PROMPT_TEMPLATE,
            n_implicit_calls_for_voting=cfg.SuccessfulCompletionClfConfig.N_CALLS_FOR_VOTING,
            max_implicit_async_calls_for_voting=cfg.SuccessfulCompletionClfConfig.MAX_ASYNC_CALL_FOR_VOTING,
            input_data_model=BacktrackerSubAgentInputData,
            max_tries_to_get_valid_response=cfg.SuccessfulCompletionClfConfig.MAX_TRIES_TO_GET_VALID_RESPONSE,
            logger=logger,
        )

    async def __call__(
        self,
        input_data: BacktrackerInputData,
        stream_handler: Optional[LmStreamHandler] = None,
        callback_after_each_lm_step: Optional[
            Callable[[List[List[InstructLmMessage]]], None]
        ] = None,
    ) -> BacktrackerReturn:

        # Prepare input data
        sub_agent_input_data = BacktrackerSubAgentInputData(
            env_state=input_data.env_state,
            olthad=input_data.olthad.stringify(
                redact_planned_subtasks_below=input_data.task_in_question.task,
                obfuscate_status_of=input_data.task_in_question.task,
            ),
            task_in_question=input_data.task_in_question.stringify(
                redact_planned_subtasks_below=input_data.task_in_question.task,
                obfuscate_status_of=input_data.task_in_question.task,
            ),
        )

        # #################################################################
        # ### Classify whether the task has been successfully completed ###
        # #################################################################

        logger.info("Checking if the task has been successfully completed...")

        return_obj = await self.successful_completion_clf(
            input_data=sub_agent_input_data, stream_handler=stream_handler
        )
        callback_after_each_lm_step(return_obj.messages)
        if (
            extract_letter_choice_from_text(
                return_obj.output_data.chosen,
                self.successful_completion_clf.multiple_choice_options,
            )
            == WAS_SUCCESSFULLY_COMPLETED_OPTIONS[BinaryCaseStr.TRUE].letter
        ):
            input_data.task_in_question.status = TaskStatus.SUCCESS
            return BacktrackerReturn(
                output_data=BacktrackerOutputData(
                    chosen_status=BacktrackedFromTaskStatus.SUCCESS,
                    retrospective=return_obj.output_data.reasoning,
                )
            )

        #####################################################################
        ### Classify whether the task has been given an exhaustive effort ###
        #####################################################################

        logger.info("Checking if an exhaustive effort was given...")

        return_obj = await self.exhaustive_effort_clf(
            input_data=sub_agent_input_data, stream_handler=stream_handler
        )
        callback_after_each_lm_step(return_obj.messages)
        if (
            extract_letter_choice_from_text(
                return_obj.output_data.chosen,
                self.exhaustive_effort_clf.multiple_choice_options,
            )
            == EFFORT_WAS_EXHAUSTIVE_OPTIONS[BinaryCaseStr.TRUE].letter
        ):
            #############################################################
            ### Classify whether the completion was a partial success ###
            #############################################################

            logger.info("Checking if the task was a partial succes (or failure)...")

            return_obj = await self.partial_success_clf(
                input_data=sub_agent_input_data, stream_handler=stream_handler
            )
            callback_after_each_lm_step(return_obj.messages)
            if (
                extract_letter_choice_from_text(
                    return_obj.output_data.chosen,
                    self.partial_success_clf.multiple_choice_options,
                )
                == WAS_PARTIAL_SUCCESS_OPTIONS[BinaryCaseStr.TRUE].letter
            ):
                return BacktrackerReturn(
                    output_data=BacktrackerOutputData(
                        chosen_status=BacktrackedFromTaskStatus.PARTIAL_SUCCESS,
                        retrospective=return_obj.output_data.reasoning,
                    )
                )
            else:
                return BacktrackerReturn(
                    output_data=BacktrackerOutputData(
                        chosen_status=BacktrackedFromTaskStatus.FAILURE,
                        retrospective=return_obj.output_data.reasoning,
                    )
                )
        else:
            ###########################################################################
            ### Classify if ancestor tasks are (still) the most worthwhile pursuits ###
            ###########################################################################

            logger.info(
                "Checking if all ancestors are still the most worthwhile pursuits..."
            )

            # Iterate through a gradual reconstruction of the olthad starting from root
            for root_node, cur_node in input_data.olthad.iter_in_progress_descendants():
                sub_agent_input_data = BacktrackerSubAgentInputData(
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
                    input_data=sub_agent_input_data, stream_handler=stream_handler
                )
                callback_after_each_lm_step(return_obj.messages)
                if (
                    extract_letter_choice_from_text(
                        return_obj.output_data.chosen,
                        self.most_worthwhile_pursuit_clf.multiple_choice_options,
                    )
                    == IS_MOST_WORTHWHILE_OPTIONS[BinaryCaseStr.FALSE].letter
                ):
                    return BacktrackerReturn(
                        output_data=BacktrackerOutputData(
                            chosen_status=BacktrackedFromTaskStatus.DROPPED,
                            retrospective=return_obj.output_data.reasoning,
                            backtrack_to=cur_node,
                        )
                    )
            # Finally, if no ancestors are worth dropping, status stays in progress
            return BacktrackerReturn(
                output_data=BacktrackerOutputData(
                    chosen_status=BacktrackedFromTaskStatus.IN_PROGRESS,
                    retrospective=None,
                )
            )
