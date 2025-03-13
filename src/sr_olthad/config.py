"""Single location for tweakable hyperparameters for the sr-OLTHAD system.

TODO: Make the UX more like hunggingface's `TrainingArguments` class & make generally
sensible static values like these be the default values.
"""

from enums import SerializationMethod

from instruct_lms import OpenAIInstructLm
from schema import InstructLm

from sr_olthad.agents.attempt_summarizer import ATTEMPT_SUMMARIZER_PROMPT_REGISTRY
from sr_olthad.agents.backtracker import (
    EXHAUSTIVE_EFFORT_CLF_PROMPT_REGISTRY,
    WORTHWHILE_PURSUIT_CLF_PROMPT_REGISTRY,
    PARTIAL_SUCCESS_CLF_PROMPT_REGISTRY,
    SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY,
)
from sr_olthad.agents.forgetter import FORGETTER_PROMPT_REGISTRY
from sr_olthad.agents.planner import PLANNER_PROMPT_REGISTRY


STRINGIFY_ENV_STATE_SERIALIZATION_METHOD: SerializationMethod = SerializationMethod.YAML


###############################
#### Sys Prompt Insertions ####
###############################


################
#### Agents ####
################


class AttemptSummarizerConfig:
    MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
    INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
    PROMPTS_VERSION = "1.0"
    PROMPTS = ATTEMPT_SUMMARIZER_PROMPT_REGISTRY[PROMPTS_VERSION]


class BacktrackerConfig:
    class ExhaustiveEffortClfConfig:
        N_CALLS_FOR_VOTING: int = 3
        MAX_ASYNC_CALL_FOR_VOTING: int = 2
        MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
        INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
        PROMPTS_VERSION = "1.0"
        PROMPTS = EXHAUSTIVE_EFFORT_CLF_PROMPT_REGISTRY[PROMPTS_VERSION]

    class MostWorthwhilePursuitClfConfig:
        N_CALLS_FOR_VOTING: int = 3
        MAX_ASYNC_CALL_FOR_VOTING: int = 2
        MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
        INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
        PROMPTS_VERSION = "1.0"
        PROMPTS = WORTHWHILE_PURSUIT_CLF_PROMPT_REGISTRY[PROMPTS_VERSION]

    class PartialSuccessClfConfig:
        N_CALLS_FOR_VOTING: int = 3
        MAX_ASYNC_CALL_FOR_VOTING: int = 2
        MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
        INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
        PROMPTS_VERSION = "1.0"
        PROMPTS = PARTIAL_SUCCESS_CLF_PROMPT_REGISTRY[PROMPTS_VERSION]

    class SuccessfulCompletionClfConfig:
        N_CALLS_FOR_VOTING: int = 3
        MAX_ASYNC_CALL_FOR_VOTING: int = 2
        MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
        INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
        PROMPTS_VERSION = "1.0"
        PROMPTS = SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY[PROMPTS_VERSION]


class ForgetterConfig:
    MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
    INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
    PROMPTS_VERSION = "1.0"
    PROMPTS = FORGETTER_PROMPT_REGISTRY[PROMPTS_VERSION]


class PlannerConfig:
    MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
    INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
    PROMPTS_VERSION = "1.0"
    PROMPTS = PLANNER_PROMPT_REGISTRY[PROMPTS_VERSION]
