from instruct_lms import OpenAIInstructLm
from schema import InstructLm

from sr_olthad.agents.attempt_summarizer import ATTEMPT_SUMMARIZER_PROMPT_REGISTRY
from sr_olthad.agents.backtracker.prompts import (
    EXHAUSTIVE_EFFORT_CLF_PROMPT_REGISTRY,
    MOST_WORTHWHILE_PURSUIT_CLF_PROMPT_REGISTRY,
    MostWorthwhilePursuitClfSysPromptInsertion,
    PARTIAL_SUCCESS_CLF_PROMPT_REGISTRY,
    SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY,
)
from sr_olthad.agents.forgetter import FORGETTER_PROMPT_REGISTRY
from sr_olthad.agents.planner import PLANNER_PROMPT_REGISTRY
from sr_olthad.enums import TaskStatus
from sr_olthad.task_node import TaskNode


BINARY_CHOICE_OPTIONS = ["A", "B"]


###############################
#### Sys Prompt Insertions ####
###############################


BINARY_CHOICE_QUESTION_OUTPUT_JSON_FORMAT = """{
    "chosen": "(str) A or B",
    "reasoning": "(str) Explanation of the nuance(s) behind your choice",
}"""

TASK_IN_QUESTION_EXAMPLE = TaskNode(
    task="1.3.1",
    description="Do a sub-sub-thing.",
    status=TaskStatus.IN_PROGRESS,
    retrospective=None,
    subtasks=None,
)

OLTHAD_EXAMPLE = TaskNode(
    task="1",
    description="Do a thing.",
    status=TaskStatus.IN_PROGRESS,
    retrospective=None,
    subtasks=[
        TaskNode(
            task="1.1",
            description="Do a sub-thing.",
            status=TaskStatus.SUCCESS,
            retrospective="This sub-thing was accomplished by doing X, Y, and Z.",
            subtasks=None,
        ),
        TaskNode(
            task="1.2",
            description="Do another sub-thing.",
            status=TaskStatus.DROPPED,
            retrospective="This sub-thing wasn't worth pusuing further in light of A, B, and C.",
            subtasks=None,
        ),
        TaskNode(
            task="1.3",
            description="Do this other sub-thing.",
            status=TaskStatus.IN_PROGRESS,
            retrospective=None,
            subtasks=[
                TASK_IN_QUESTION_EXAMPLE,
                TaskNode(
                    task="1.3.2",
                    description="Do another sub-sub-thing.",
                    status=TaskStatus.PLANNED,
                    retrospective=None,
                    subtasks=None,
                ),
            ],
        ),
        TaskNode(
            task="1.4",
            description="Do yet another sub-thing.",
            status=TaskStatus.PLANNED,
            retrospective=None,
            subtasks=None,
        ),
    ],
)


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
        N_CALLS_FOR_VOTING: int = 3
        MAX_ASYNC_CALL_FOR_VOTING: int = 2
        MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
        INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
        PROMPTS_VERSION = "1.0"
        USER_PROMPT_TEMPLATE = EXHAUSTIVE_EFFORT_CLF_PROMPT_REGISTRY[
            PROMPTS_VERSION
        ].user_prompt_template
        # TODO: Actually render
        SYS_PROMPT = EXHAUSTIVE_EFFORT_CLF_PROMPT_REGISTRY[
            PROMPTS_VERSION
        ].sys_prompt_template.render()

    class MostWorthwhilePursuitClfConfig:
        N_CALLS_FOR_VOTING: int = 3
        MAX_ASYNC_CALL_FOR_VOTING: int = 2
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
                MostWorthwhilePursuitClfSysPromptInsertion.OLTHAD_EXAMPLE: OLTHAD_EXAMPLE,
                MostWorthwhilePursuitClfSysPromptInsertion.TASK_IN_QUESTION_EXAMPLE: TASK_IN_QUESTION_EXAMPLE,
                MostWorthwhilePursuitClfSysPromptInsertion.OUTPUT_JSON_FORMAT: BINARY_CHOICE_QUESTION_OUTPUT_JSON_FORMAT,
            }
        )

    class PartialSuccessClfConfig:
        N_CALLS_FOR_VOTING: int = 3
        MAX_ASYNC_CALL_FOR_VOTING: int = 2
        MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
        INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
        PROMPTS_VERSION = "1.0"
        USER_PROMPT_TEMPLATE = PARTIAL_SUCCESS_CLF_PROMPT_REGISTRY[
            PROMPTS_VERSION
        ].user_prompt_template
        # TODO: Actually render
        SYS_PROMPT = PARTIAL_SUCCESS_CLF_PROMPT_REGISTRY[
            PROMPTS_VERSION
        ].sys_prompt_template.render()

    class SuccessfulCompletionClfConfig:
        N_CALLS_FOR_VOTING: int = 3
        MAX_ASYNC_CALL_FOR_VOTING: int = 2
        MAX_TRIES_TO_GET_VALID_RESPONSE: int = 3
        INSTRUCT_LM: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
        PROMPTS_VERSION = "1.0"
        USER_PROMPT_TEMPLATE = SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY[
            PROMPTS_VERSION
        ].user_prompt_template
        # TODO: Actually render
        SYS_PROMPT = SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY[
            PROMPTS_VERSION
        ].sys_prompt_template.render()


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
