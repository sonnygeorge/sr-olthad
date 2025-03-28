"""Dataclasses, types and misc. enums for the sr_olthad package."""

from dataclasses import dataclass
from enum import StrEnum
from typing import TypeAlias

from jinja2 import Template
from pydantic import BaseModel

##################################################################
### Enum of readable strings to identify sr-OLTHAD's LM agents ###
##################################################################


class LmAgentName(StrEnum):
    ATTEMPT_SUMMARIZER = "Attempt Summarizer"
    FORGETTER = "Forgetter"
    PLANNER = "Planner"
    EXHAUSTIVE_EFFORT_CLF = "Backtracker: Exhaustive Effort Classifer"
    MOST_WORTHWHILE_PURSUIT_CLF = "Backtracker: Most Worthwhile Pursuit Classifier"
    PARTIAL_SUCCESS_CLF = "Backtracker: Partial Success Classifier"
    SUCCESSFUL_COMPLETION_CLF = "Backtracker: Successful Completion Classifier"


########################
### TaskStatus enums ###
########################


class AttemptedTaskStatus(StrEnum):
    """Statuses that indicate that a task was attempted."""

    SUCCESS = "Attempted (success)"
    PARTIAL_SUCCESS = "Attempted (partial success)"
    FAILURE = "Attempted (failure)"


class BacktrackedFromTaskStatus(StrEnum):
    """Statuses that warrant backtracking or indicate that backtracking occured."""

    SUCCESS = AttemptedTaskStatus.SUCCESS
    PARTIAL_SUCCESS = AttemptedTaskStatus.PARTIAL_SUCCESS
    FAILURE = AttemptedTaskStatus.FAILURE
    DROPPED = "Dropped"


class TaskStatus(StrEnum):
    """All possible statuses for a task"""

    IN_PROGRESS = "In progress"
    SUCCESS = AttemptedTaskStatus.SUCCESS
    PARTIAL_SUCCESS = AttemptedTaskStatus.PARTIAL_SUCCESS
    DROPPED = BacktrackedFromTaskStatus.DROPPED
    FAILURE = AttemptedTaskStatus.FAILURE
    PLANNED = "Tentatively planned"


######################
### Prompt-related ###
######################


class CommonSysPromptInputData(BaseModel):
    """Fields/data dynamically rendered into the system prompt for all lm agents."""

    domain_specific_insert: str | None = None


class CommonSysPromptInputFields(StrEnum):
    """
    Enum of the fields in the CommonSysPromptInputData model.

    NOTE: These strings must be identical to the above field names in the
    `CommonSysPromptInputData` model.
    """

    DOMAIN_SPECIFIC_INSERT = "domain_specific_insert"


class CommonUserPromptInputData(BaseModel):
    """
    Fields/data dynamically rendered into the user prompt all lm agents.

    Attributes:
        env_state (str): PRE-STRINGIFIED current environment state.
        olthad (str): PRE-STRINGIFIED root task node of the OLTHAD being traversed.
        task_in_question (str): PRE-STRINGIFIED task node we're considering backtracking
            from.
    """

    env_state: str
    olthad: str
    task_in_question: str


class CommonUserPromptInputFields(StrEnum):
    """
    Enum of the fields in the CommonUserPromptInputData model.

    NOTE: These strings must be identical to the above field names in the
    `CommonUserPromptInputData` model.
    """

    ENV_STATE = "env_state"
    OLTHAD = "olthad"
    TASK_IN_QUESTION = "task_in_question"


@dataclass
class SingleTurnPromptTemplates:
    user_prompt_template: Template
    sys_prompt_template: Template | None = None


PromptVersionString: TypeAlias = str
PromptRegistry = dict[PromptVersionString, SingleTurnPromptTemplates]


########################################
### Multiple-choice question options ###
########################################


LetterStr: TypeAlias = str


class MultipleChoiceQuestionOption(BaseModel, frozen=True):
    """Immutable config for an option in a multiple-choice question."""

    letter: LetterStr
    text: str


BinaryChoiceOptions = dict[bool, MultipleChoiceQuestionOption]
NonBinaryChoiceOptions = dict[str, MultipleChoiceQuestionOption]
