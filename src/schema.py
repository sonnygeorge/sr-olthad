from abc import ABC, abstractmethod
from typing import (
    Any,
    Callable,
    Dict,
    List,
    Optional,
    Set,
    TypeAlias,
    TypedDict,
)

from jinja2 import Template
from pydantic import BaseModel

from enums import InstructLmChatRole


JsonSerializable = (
    None
    | bool
    | int
    | float
    | str
    | List["JsonSerializable"]
    | Dict[str, "JsonSerializable"]
)

#################
#### Prompts ####
#################


class SingleTurnPrompts(BaseModel):
    sys_prompt: Optional[str] = None
    user_prompt: Template


# E.g. "1.0" where the 1st number changes for major strategy changes
PromptVersionString: TypeAlias = str
PromptRegistry = Dict[PromptVersionString, SingleTurnPrompts]


######################
#### Instruct LMs ####
######################


class InstructLmMessage(TypedDict):
    role: InstructLmChatRole
    content: str


class InstructLm(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: List[InstructLmMessage],
        stream_handler: Optional[Callable[[str], Any]],
        **kwargs
    ) -> str:
        pass


################
#### Agents ####
################


class MultipleChoiceQuestionAgentOutputData(BaseModel):
    chosen: str
    reasoning: str


class AgentReturn(BaseModel):
    output_data: BaseModel


class InstructLmAgentReturn(AgentReturn):
    output_data: BaseModel
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class MultipleChoiceQuestionAgentReturn(InstructLmAgentReturn):
    output_data: MultipleChoiceQuestionAgentOutputData
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class Agent(ABC):
    """
    An "agent" (typically LM-powered) that takes a `pydantic.BaseModel` as input data and
    returns some object with an `output_data` attribute that is a `pydantic.BaseModel`.
    """

    @abstractmethod
    async def __call__(self, input_data: BaseModel, **kwargs) -> AgentReturn:
        pass


class InstructLmAgent(Agent):
    """
    An `Agent` that uses a single-turn conversation with an instruction-tuned LM for
    inferencing an output data object.
    """

    @abstractmethod
    async def __call__(self, input_data: BaseModel, **kwargs) -> InstructLmAgentReturn:
        pass


class MultipleChoiceQuestionAgent(InstructLmAgent):
    """A `InstructLmAgent` that answers a multiple-choice question."""

    @property
    @abstractmethod
    def multiple_choice_options(self) -> Set[str]:
        pass

    @abstractmethod
    async def __call__(
        self, input_data: BaseModel, **kwargs
    ) -> MultipleChoiceQuestionAgentReturn:
        pass
