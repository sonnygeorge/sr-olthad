from dataclasses import dataclass
from enum import StrEnum
from typing import Dict, Generator, List, Optional, TypeAlias

from jinja2 import Template
from pydantic import BaseModel

LetterStr: TypeAlias = str


class MultipleChoiceQuestionOption(BaseModel, frozen=True):
    """Immutable config for an option in a multiple-choice question."""

    letter: LetterStr
    text: str


BinaryChoiceOptions = Dict[bool, MultipleChoiceQuestionOption]
NonBinaryChoiceOptions = Dict[str, MultipleChoiceQuestionOption]


@dataclass
class SingleTurnPromptTemplates:
    user_prompt_template: Template
    sys_prompt_template: Optional[Template] = None


# E.g. "1.0" where the 1st number changes for _major_ strategy changes
PromptVersionString: TypeAlias = str
PromptRegistry = Dict[PromptVersionString, SingleTurnPromptTemplates]


DiffLines: TypeAlias = List[str]
GetApprovalBeforeUpdateGenerator: TypeAlias = Generator[DiffLines, bool, None]


class AgentName(StrEnum):
    """Enum of agent names."""

    ATTEMPT_SUMMARIZER = "Attempt Summarizer"
    BACKTRACKER = "Backtracker"
    FORGETTER = "Forgetter"
    PLANNER = "Planner"
    EXHAUSTIVE_EFFORT_CLF = "Exhaustive Effort Classifer"
    MOST_WORTHWHILE_PURSUIT_CLF = "Most Worthwhile Pursuit Classifier"
    PARTIAL_SUCCESS_CLF = "Partial Success Classifier"
    SUCCESSFUL_COMPLETION_CLF = "Successful Completion Classifier"
