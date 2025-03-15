from dataclasses import dataclass
from typing import Dict, Optional, TypeAlias

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
