from loguru import logger
from pydantic import BaseModel

from schema import Agent, AgentReturn
from single_turn_chat_agent import SingleTurnChatMultipleChoiceAgent
from sr_olthad.agents.config import BacktrackerConfig as cfg
from sr_olthad.agents.config import BINARY_CHOICE_OPTIONS
from sr_olthad.enums import BacktrackedFromTaskStatus
from sr_olthad.task_node import TaskNode


class BacktrackerInputData(BaseModel):
    env_state: str
    olthad: TaskNode  # I.e., the root task node w/ all the descendants


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
            multiple_choice_options=BINARY_CHOICE_OPTIONS,
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
            multiple_choice_options=BINARY_CHOICE_OPTIONS,
            sys_prompt=cfg.MostWorthwhilePursuitClfConfig.SYS_PROMPT,
            user_prompt_template=cfg.MostWorthwhilePursuitClfConfig.USER_PROMPT_TEMPLATE,
            n_implicit_calls_for_voting=cfg.MostWorthwhilePursuitClfConfig.N_CALLS_FOR_VOTING,
            max_implicit_async_calls_for_voting=cfg.MostWorthwhilePursuitClfConfig.MAX_ASYNC_CALL_FOR_VOTING,
            input_data_model=BacktrackerInputData,  # FIXME
            max_tries_to_get_valid_response=cfg.MostWorthwhilePursuitClfConfig.MAX_TRIES_TO_GET_VALID_RESPONSE,
        )
        # Initialize partial success classifier
        self.partial_success_clf: SingleTurnChatMultipleChoiceAgent[
            BacktrackerInputData
        ] = SingleTurnChatMultipleChoiceAgent(
            instruct_lm=cfg.PartialSuccessClfConfig.INSTRUCT_LM,
            multiple_choice_options=BINARY_CHOICE_OPTIONS,
            sys_prompt=cfg.PartialSuccessClfConfig.SYS_PROMPT,
            user_prompt_template=cfg.PartialSuccessClfConfig.USER_PROMPT_TEMPLATE,
            n_implicit_calls_for_voting=cfg.PartialSuccessClfConfig.N_CALLS_FOR_VOTING,
            max_implicit_async_calls_for_voting=cfg.PartialSuccessClfConfig.MAX_ASYNC_CALL_FOR_VOTING,
            input_data_model=BacktrackerInputData,  # FIXME
            max_tries_to_get_valid_response=cfg.PartialSuccessClfConfig.MAX_TRIES_TO_GET_VALID_RESPONSE,
        )
        # Initialize successful completion classifier
        self.successful_completion_clf: SingleTurnChatMultipleChoiceAgent[
            BacktrackerInputData
        ] = SingleTurnChatMultipleChoiceAgent(
            instruct_lm=cfg.SuccessfulCompletionClfConfig.INSTRUCT_LM,
            multiple_choice_options=BINARY_CHOICE_OPTIONS,
            sys_prompt=cfg.SuccessfulCompletionClfConfig.SYS_PROMPT,
            user_prompt_template=cfg.SuccessfulCompletionClfConfig.USER_PROMPT_TEMPLATE,
            n_implicit_calls_for_voting=cfg.SuccessfulCompletionClfConfig.N_CALLS_FOR_VOTING,
            max_implicit_async_calls_for_voting=cfg.SuccessfulCompletionClfConfig.MAX_ASYNC_CALL_FOR_VOTING,
            input_data_model=BacktrackerInputData,  # FIXME
            max_tries_to_get_valid_response=cfg.SuccessfulCompletionClfConfig.MAX_TRIES_TO_GET_VALID_RESPONSE,
        )

    async def __call__(self, input_data: BacktrackerInputData) -> BacktrackerReturn:
        pass  # TODO
