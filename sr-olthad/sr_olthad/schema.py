"""Dataclasses, types and misc. enums for the sr_olthad package."""

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol, TypeAlias

from jinja2 import Template
from pydantic import BaseModel

##################################################################
### Enum of readable strings to identify sr-OLTHAD's LM agents ###
##################################################################


class LmAgentName(StrEnum):
    ATTEMPT_SUMMARIZER = "Attempt Summarizer"
    FORGETTER = "Forgetter"
    PLANNER = "Planner"
    EXHAUSTIVE_EFFORT_CLF = "Backtracker: Exhaustive Effort Classifier"
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
    """Statuses that warrant backtracking or indicate that backtracking occurred."""

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


#################################
### Dynamic prompt input data ###
#################################


class DomainSpecificSysPromptInputData(BaseModel):
    """Fields/data dynamically rendered into the system prompt (of all lm agents)."""

    lm_role_as_verb_phrase: str
    domain_exposition: str


class DomainSpecificSysPromptInputFields(StrEnum):
    """
    Enum of the fields in the DomainSpecificSysPromptInputData model.

    NOTE: These strings must be identical to the above field names in the
    `CommonSysPromptInputData` model.
    """

    LM_ROLE_AS_VERB_PHRASE = "lm_role_as_verb_phrase"
    DOMAIN_EXPOSITION = "domain_exposition"


class UserPromptInputData(BaseModel):
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


class UserPromptInputFields(StrEnum):
    """
    Enum of the fields in the CommonUserPromptInputData model.

    NOTE: These strings must be identical to the above field names in the
    `CommonUserPromptInputData` model.
    """

    ENV_STATE = "env_state"
    OLTHAD = "olthad"
    TASK_IN_QUESTION = "task_in_question"


##########################
### Callable protocols ###
##########################


class GetDomainSpecificSysPromptInputData(Protocol):
    """
    Callable that, given knowledge about what LM agent is being invoked and what its
    current user-prompt input data is (e.g. the task in question), returns data (e.g.
    situation-relevant in-context examples) to be dynamically rendered into the system
    prompt at inference time.

    Args:
        lm_agent_name (LmAgentName): The name of the LM agent.
        input_data (UserPromptInputData): The input data for the current invocation
            of the LM agent.

    Returns:
        DomainSpecificSysPromptInputData: The data to be rendered into the system prompt.
    """

    def __call__(
        self, lm_agent_name: LmAgentName, user_prompt_input_data: UserPromptInputData
    ) -> DomainSpecificSysPromptInputData: ...


######################################
### Some more prompt-related stuff ###
######################################


@dataclass
class SingleTurnPromptTemplates:
    user_prompt_template: Template
    sys_prompt_template: Template | None = None


PromptVersionString: TypeAlias = str
PromptRegistry = dict[PromptVersionString, SingleTurnPromptTemplates]

LetterStr: TypeAlias = str


class MultipleChoiceQuestionOption(BaseModel, frozen=True):
    """Immutable config for an option in a multiple-choice question."""

    letter: LetterStr
    text: str


BinaryChoiceOptions = dict[bool, MultipleChoiceQuestionOption]
NonBinaryChoiceOptions = dict[str, MultipleChoiceQuestionOption]
