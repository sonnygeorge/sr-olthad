from typing import Protocol

from sr_olthad.common.lms import OpenAIInstructLm
from sr_olthad.common.schema import InstructLm

# General config


class SrOlthadCfg:
    JSON_DUMPS_INDENT = 3


# Agent configs


class LmAgentConfig(Protocol):
    MAX_TRIES_TO_GET_VALID_LM_RESPONSE: int
    INSTRUCT_LM: InstructLm
    PROMPTS_VERSION: str


class AttemptSummarizerCfg:
    MAX_TRIES_TO_GET_VALID_LM_RESPONSE: int = 3
    INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-4o-mini-2024-07-18")
    PROMPTS_VERSION = "1.0"


class BacktrackerCfg:
    class ExhaustiveEffortClf:
        N_CALLS_FOR_VOTING: int = 1
        MAX_ASYNC_CALLS_FOR_VOTING: int = 5
        MAX_TRIES_TO_GET_VALID_LM_RESPONSE: int = 3
        INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-4o-mini-2024-07-18")
        PROMPTS_VERSION = "1.0"

    class MostWorthwhilePursuitClfCfg:
        N_CALLS_FOR_VOTING: int = 1
        MAX_ASYNC_CALLS_FOR_VOTING: int = 5
        MAX_TRIES_TO_GET_VALID_LM_RESPONSE: int = 3
        INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-4o-mini-2024-07-18")
        PROMPTS_VERSION = "1.0"

    class PartialSuccessClfCfg:
        N_CALLS_FOR_VOTING: int = 1
        MAX_ASYNC_CALLS_FOR_VOTING: int = 5
        MAX_TRIES_TO_GET_VALID_LM_RESPONSE: int = 3
        INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-4o-mini-2024-07-18")
        PROMPTS_VERSION = "1.0"

    class SuccessfulCompletionClfCfg:
        N_CALLS_FOR_VOTING: int = 2
        MAX_ASYNC_CALLS_FOR_VOTING: int = 5
        MAX_TRIES_TO_GET_VALID_LM_RESPONSE: int = 3
        INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-4o-mini-2024-07-18")
        PROMPTS_VERSION = "1.0"


class ForgetterCfg:
    MAX_TRIES_TO_GET_VALID_LM_RESPONSE: int = 3
    INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-4o-mini-2024-07-18")
    PROMPTS_VERSION = "1.0"


class PlannerCfg:
    MAX_TRIES_TO_GET_VALID_LM_RESPONSE: int = 3
    INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-4o-mini-2024-07-18")
    PROMPTS_VERSION = "1.0"
