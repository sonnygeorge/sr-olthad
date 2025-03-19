from abc import ABC, abstractmethod
from enum import StrEnum
from typing import (
    Any,
    Callable,
    List,
    Optional,
    Protocol,
    TypeAlias,
    TypedDict,
)

from pydantic import BaseModel

# Agent


# NOTE: The idea behind this pattern was I wanted to separate what is thought of as
# an agent's "output data" from potential other artifacts (e.g., the "messages" from a
# `SingleTurnChatAgent`). There are probably other (cleaner?) ways to do this, but this
# is what I went with.


class HasOutputData(Protocol):
    output_data: BaseModel


class Agent(ABC):
    """
    Any async `Callable`  that takes any sort of inputs and returns some object with at
    least an `output_data` attribute that is a `pydantic.BaseModel`.
    """

    @abstractmethod
    async def __call__(self, *args, **kwargs) -> HasOutputData:
        pass


# InstructLm


class InstructLmChatRole(StrEnum):
    SYS = "system"
    USER = "user"
    ASSISTANT = "assistant"


class InstructLmMessage(TypedDict):
    role: InstructLmChatRole
    content: str


# NOTE: Whenever an agent could be potentially wrapped w/ `with_implicit_async_voting`
# decorator, attributes of the return object as well as the `output_data` attribute of the
# return object should be thought of as potentially nested.
# This is weird, but I didn't want to rewrite voting logic over and over again so my
# idea was to put it in that decorator.

PotentiallyNestedInstructLmMessages: TypeAlias = (
    List[InstructLmMessage] | List[List[InstructLmMessage]]
)


LmStreamHandler: TypeAlias = Callable[[str], Any]


class InstructLm(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: List[InstructLmMessage],
        stream_handler: Optional[LmStreamHandler] = None,
        **kwargs
    ) -> str:
        pass


class LmStreamsHandler(ABC):
    @abstractmethod
    def __call__(self, chunk_str: str, stream_idx: Optional[int] = None):
        """A `Callable` that handles streaming potentially multiple LM streams.

        Args:
            chunk_str (str): The string chunk of LM output.
            stream_idx (Optional[int]): When the stream is one amongst many
                asynchronous LM calls, this is the number/index of which call the stream
                chunk is coming from. Defaults to None. See `with_implicit_async_voting`.
        """
        pass
