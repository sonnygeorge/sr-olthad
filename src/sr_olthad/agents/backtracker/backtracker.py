from loguru import logger
from pydantic import BaseModel
from typing import Optional, Callable

from enums import BinaryCaseStr
from schema import Agent, AgentReturn, LmStreamHandler
from single_turn_chat_agent import SingleTurnChatMultipleChoiceAgent
from sr_olthad.agents.config import BacktrackerConfig as cfg
from sr_olthad.agents.backtracker.prompts import (
    WAS_SUCCESSFULLY_COMPLETED_OPTIONS,
    IS_MOST_WORTHWHILE_OPTIONS,
    EFFORT_WAS_EXHAUSTIVE_OPTIONS,
    WAS_PARTIAL_SUCCESS_OPTIONS,
)
from sr_olthad.enums import BacktrackedFromTaskStatus
from sr_olthad.task_node import TaskNode
from utils import extract_letter_from_multiple_choice_question_agent_output_data


class BacktrackerInputData(BaseModel):
    env_state: str
    olthad: TaskNode  # The root node w/ all the descendants
    task_in_question: TaskNode  # The node we're considering backtracking from


class BacktrackerOutputData(BaseModel):
    chosen_status: BacktrackedFromTaskStatus
    retrospective: str


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
            input_data_model=BacktrackerInputData,  # FIXME
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
            input_data_model=BacktrackerInputData,  # FIXME
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
            input_data_model=BacktrackerInputData,  # FIXME
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
            input_data_model=BacktrackerInputData,  # FIXME
            max_tries_to_get_valid_response=cfg.SuccessfulCompletionClfConfig.MAX_TRIES_TO_GET_VALID_RESPONSE,
            logger=logger,
        )

    async def __call__(
        self,
        input_data: BacktrackerInputData,
        stream_handler: Optional[LmStreamHandler] = None,
        callback_after_each_lm_step: Callable[[], None] = None,
    ) -> BacktrackerReturn:
        logger.info("Backtracker called...")
        # Remove this because it confuses LMs!
        input_data.task_in_question.status = None

        # Classify whether the task has been successfully completed
        return_obj = await self.successful_completion_clf(
            input_data=input_data, stream_handler=stream_handler
        )
        callback_after_each_lm_step()
        if (
            extract_letter_from_multiple_choice_question_agent_output_data(
                return_obj.output_data,
                self.successful_completion_clf.multiple_choice_options,
            )
            == WAS_SUCCESSFULLY_COMPLETED_OPTIONS[BinaryCaseStr.TRUE].letter
        ):
            return BacktrackerReturn(
                output_data=BacktrackerOutputData(
                    chosen_status=BacktrackedFromTaskStatus.SUCCESS,
                    retrospective=return_obj.output_data.reasoning,
                )
            )
