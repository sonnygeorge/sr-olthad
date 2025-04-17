from typing import Protocol

from sr_olthad.framework.lms import GroqInstructLm, OpenAIInstructLm, HuggingFaceInstructLm, DeepSeekInstructLm
from sr_olthad.framework.schema import InstructLm

# General config


class SrOlthadCfg:
    JSON_DUMPS_INDENT = 3


# Agent configs


class LmAgentConfig(Protocol):
    MAX_TRIES_TO_GET_VALID_LM_RESPONSE: int
    INSTRUCT_LM: InstructLm
    PROMPTS_VERSION: str


class AttemptSummarizerCfg:
    MAX_TRIES_TO_GET_VALID_LM_RESPONSE: int = 5
    INSTRUCT_LM: InstructLm = GroqInstructLm(model="llama-3.1-8b-instant")#GroqInstructLm(model="llama-3.1-8b-instant")#GroqInstructLm(model="llama-3.1-8b-instant")
    PROMPTS_VERSION = "1.0"


class BacktrackerCfg:
    class ExhaustiveEffortClf:
        N_CALLS_FOR_VOTING: int = 1
        MAX_ASYNC_CALLS_FOR_VOTING: int = 5
        MAX_TRIES_TO_GET_VALID_LM_RESPONSE: int = 7
        INSTRUCT_LM: InstructLm =  GroqInstructLm(model="llama-3.1-8b-instant")#GroqInstructLm(model="llama-3.1-8b-instant")
        PROMPTS_VERSION = "1.0"

    class MostWorthwhilePursuitClfCfg:
        N_CALLS_FOR_VOTING: int = 1
        MAX_ASYNC_CALLS_FOR_VOTING: int = 5
        MAX_TRIES_TO_GET_VALID_LM_RESPONSE: int = 5
        INSTRUCT_LM: InstructLm = GroqInstructLm(model="llama-3.1-8b-instant")#GroqInstructLm(model="llama-3.1-8b-instant")
        PROMPTS_VERSION = "1.0"

    class PartialSuccessClfCfg:
        N_CALLS_FOR_VOTING: int = 1
        MAX_ASYNC_CALLS_FOR_VOTING: int = 5
        MAX_TRIES_TO_GET_VALID_LM_RESPONSE: int = 7
        INSTRUCT_LM: InstructLm =  GroqInstructLm(model="llama-3.1-8b-instant")#GroqInstructLm(model="llama-3.1-8b-instant")
        PROMPTS_VERSION = "1.0"

    class SuccessfulCompletionClfCfg:
        N_CALLS_FOR_VOTING: int = 1
        MAX_ASYNC_CALLS_FOR_VOTING: int = 5
        MAX_TRIES_TO_GET_VALID_LM_RESPONSE: int = 7
        INSTRUCT_LM: InstructLm =  GroqInstructLm(model="llama-3.1-8b-instant")#GroqInstructLm(model="llama-3.1-8b-instant")
        PROMPTS_VERSION = "1.0"


class ForgetterCfg:
    MAX_TRIES_TO_GET_VALID_LM_RESPONSE: int = 5
    INSTRUCT_LM: InstructLm = GroqInstructLm(model="llama-3.1-8b-instant")#GroqInstructLm(model="llama-3.1-8b-instant")
    PROMPTS_VERSION = "1.0"


class PlannerCfg:
    MAX_TRIES_TO_GET_VALID_LM_RESPONSE: int = 5
    INSTRUCT_LM: InstructLm = GroqInstructLm(model="llama-3.1-8b-instant")#GroqInstructLm(model="llama-3.1-8b-instant")
    PROMPTS_VERSION = "1.0"
