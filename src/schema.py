from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import (
    Dict,
    List,
    Optional,
    TypeAlias,
    TypedDict,
)

from jinja2 import Template
from pydantic import BaseModel

from enums import InstructLmChatRole, BinaryCaseStr


JsonSerializable = (
    None
    | bool
    | int
    | float
    | str
    | List["JsonSerializable"]
    | Dict[str, "JsonSerializable"]
)


#####################
#### Instruct LM ####
#####################


class InstructLmMessage(TypedDict):
    role: InstructLmChatRole
    content: str


class LmStreamHandler(ABC):
    @abstractmethod
    def __call__(self, chunk_str: str, async_call_idx: Optional[int] = None):
        """A `Callable` that handles streaming LM output.

        Args:
            chunk_str (str): The string chunk of LM output.
            async_call_idx (Optional[int], optional): When the stream is one amongst many
                asynchronous LM calls, this is the number/index of which call the stream
                chunk is coming from. Defaults to None.
        """
        pass


class InstructLm(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: List[InstructLmMessage],
        stream_handler: Optional[LmStreamHandler],
        **kwargs
    ) -> str:
        pass


####################
#### Base Agent ####
####################


class AgentReturn(BaseModel):
    output_data: BaseModel


class Agent(ABC):
    """
    An "agent" (typically LM-powered) that takes a `pydantic.BaseModel` as input data and
    returns some object with an `output_data` attribute that is a `pydantic.BaseModel`.
    """

    @abstractmethod
    async def __call__(self, input_data: BaseModel, **kwargs) -> AgentReturn:
        pass


##########################
#### InstructLm Agent ####
##########################


class InstructLmAgentReturn(AgentReturn):
    output_data: BaseModel
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class InstructLmAgent(Agent):
    """
    An `Agent` that uses a single-turn conversation with an instruction-tuned LM for
    inferencing an output data object.
    """

    @abstractmethod
    async def __call__(self, input_data: BaseModel, **kwargs) -> InstructLmAgentReturn:
        pass


########################################
#### Multiple Choice Question Agent ####
########################################


class MultipleChoiceQuestionAgentOutputData(BaseModel):
    chosen: str
    reasoning: str


class MultipleChoiceQuestionAgentReturn(InstructLmAgentReturn):
    output_data: MultipleChoiceQuestionAgentOutputData
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class MultipleChoiceQuestionAgentOption(BaseModel, frozen=True):
    """Immutable configuration type for options in a multiple-choice question."""

    letter: str
    text: str


BinaryChoiceOptions = Dict[BinaryCaseStr, MultipleChoiceQuestionAgentOption]
NonBinaryChoiceOptions = Dict[str, MultipleChoiceQuestionAgentOption]


class MultipleChoiceQuestionAgent(InstructLmAgent):
    """A `InstructLmAgent` that answers a multiple-choice question."""

    @property
    @abstractmethod
    def multiple_choice_options(self) -> BinaryChoiceOptions | NonBinaryChoiceOptions:
        pass

    @abstractmethod
    async def __call__(
        self, input_data: BaseModel, **kwargs
    ) -> MultipleChoiceQuestionAgentReturn:
        pass


#################
#### Prompts ####
#################


@dataclass
class SingleTurnPromptTemplates:
    user_prompt_template: Template
    sys_prompt_template: Optional[Template] = None


# E.g. "1.0" where the 1st number changes for _major_ strategy changes
PromptVersionString: TypeAlias = str
PromptRegistry = Dict[PromptVersionString, SingleTurnPromptTemplates]
