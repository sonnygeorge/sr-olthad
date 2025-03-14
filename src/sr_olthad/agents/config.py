from instruct_lms import OpenAIInstructLm
from schema import InstructLm

from sr_olthad.agents.attempt_summarizer import ATTEMPT_SUMMARIZER_PROMPT_REGISTRY
from sr_olthad.agents.backtracker.prompts import (
    EXHAUSTIVE_EFFORT_CLF_PROMPT_REGISTRY,
    MOST_WORTHWHILE_PURSUIT_CLF_PROMPT_REGISTRY,
    PARTIAL_SUCCESS_CLF_PROMPT_REGISTRY,
    SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY,
    EXHAUSTIVE_EFFORT_CLF_SYS_PROMPT_INSERTION_FIELDS,
    MOST_WORTHWHILE_PURSUIT_CLF_SYS_PROMPT_INSERTION_FIELDS,
    PARTIAL_SUCCESS_CLF_SYS_PROMPT_INSERTION_FIELDS,
    SUCCESSFUL_COMPLETION_CLF_SYS_PROMPT_INSERTION_FIELDS,
)
from sr_olthad.agents.forgetter import FORGETTER_PROMPT_REGISTRY
from sr_olthad.agents.planner import PLANNER_PROMPT_REGISTRY
from sr_olthad.enums import TaskStatus
from sr_olthad.prompts import SYS_PROMPT_INSERTIONS_REGISTRY
from sr_olthad.task_node import TaskNode


################
#### Agents ####
################


class AttemptSummarizerConfig:
    MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
    INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
    PROMPTS_VERSION = "1.0"
    USER_PROMPT_TEMPLATE = ATTEMPT_SUMMARIZER_PROMPT_REGISTRY[
        PROMPTS_VERSION
    ].user_prompt_template
    # TODO: Actually render
    SYS_PROMPT = ATTEMPT_SUMMARIZER_PROMPT_REGISTRY[
        PROMPTS_VERSION
    ].sys_prompt_template.render()


class BacktrackerConfig:
    class ExhaustiveEffortClfConfig:
        N_CALLS_FOR_VOTING: int = 1
        MAX_ASYNC_CALL_FOR_VOTING: int = 5
        MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
        INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
        PROMPTS_VERSION = "1.0"
        USER_PROMPT_TEMPLATE = EXHAUSTIVE_EFFORT_CLF_PROMPT_REGISTRY[
            PROMPTS_VERSION
        ].user_prompt_template
        # TODO: Actually render
        SYS_PROMPT = EXHAUSTIVE_EFFORT_CLF_PROMPT_REGISTRY[
            PROMPTS_VERSION
        ].sys_prompt_template.render(
            **{
                field: SYS_PROMPT_INSERTIONS_REGISTRY[field]
                for field in EXHAUSTIVE_EFFORT_CLF_SYS_PROMPT_INSERTION_FIELDS
            }
        )

    class MostWorthwhilePursuitClfConfig:
        N_CALLS_FOR_VOTING: int = 1
        MAX_ASYNC_CALL_FOR_VOTING: int = 5
        MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
        INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
        PROMPTS_VERSION = "1.0"
        USER_PROMPT_TEMPLATE = MOST_WORTHWHILE_PURSUIT_CLF_PROMPT_REGISTRY[
            PROMPTS_VERSION
        ].user_prompt_template
        SYS_PROMPT = MOST_WORTHWHILE_PURSUIT_CLF_PROMPT_REGISTRY[
            PROMPTS_VERSION
        ].sys_prompt_template.render(
            **{
                field: SYS_PROMPT_INSERTIONS_REGISTRY[field]
                for field in MOST_WORTHWHILE_PURSUIT_CLF_SYS_PROMPT_INSERTION_FIELDS
            }
        )

    class PartialSuccessClfConfig:
        N_CALLS_FOR_VOTING: int = 1
        MAX_ASYNC_CALL_FOR_VOTING: int = 5
        MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
        INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
        PROMPTS_VERSION = "1.0"
        USER_PROMPT_TEMPLATE = PARTIAL_SUCCESS_CLF_PROMPT_REGISTRY[
            PROMPTS_VERSION
        ].user_prompt_template
        # TODO: Actually render
        SYS_PROMPT = PARTIAL_SUCCESS_CLF_PROMPT_REGISTRY[
            PROMPTS_VERSION
        ].sys_prompt_template.render(
            **{
                field: SYS_PROMPT_INSERTIONS_REGISTRY[field]
                for field in PARTIAL_SUCCESS_CLF_SYS_PROMPT_INSERTION_FIELDS
            }
        )

    class SuccessfulCompletionClfConfig:
        N_CALLS_FOR_VOTING: int = 1
        MAX_ASYNC_CALL_FOR_VOTING: int = 5
        MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
        INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-4o-mini-2024-07-18")
        PROMPTS_VERSION = "1.0"
        USER_PROMPT_TEMPLATE = SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY[
            PROMPTS_VERSION
        ].user_prompt_template
        # TODO: Actually render
        SYS_PROMPT = SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY[
            PROMPTS_VERSION
        ].sys_prompt_template.render(
            **{
                field: SYS_PROMPT_INSERTIONS_REGISTRY[field]
                for field in SUCCESSFUL_COMPLETION_CLF_SYS_PROMPT_INSERTION_FIELDS
            }
        )


class ForgetterConfig:
    MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
    INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
    PROMPTS_VERSION = "1.0"
    USER_PROMPT_TEMPLATE = FORGETTER_PROMPT_REGISTRY[
        PROMPTS_VERSION
    ].user_prompt_template
    # TODO: Actually render
    SYS_PROMPT = FORGETTER_PROMPT_REGISTRY[PROMPTS_VERSION].sys_prompt_template.render()


class PlannerConfig:
    MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
    INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
    PROMPTS_VERSION = "1.0"
    USER_PROMPT_TEMPLATE = PLANNER_PROMPT_REGISTRY[PROMPTS_VERSION].user_prompt_template
    # TODO: Actually render
    SYS_PROMPT = PLANNER_PROMPT_REGISTRY[PROMPTS_VERSION].sys_prompt_template.render()
