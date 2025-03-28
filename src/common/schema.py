from abc import ABC, abstractmethod
from collections.abc import Callable
from enum import StrEnum
from typing import Any, Protocol, TypeAlias

from pydantic import BaseModel
from typing_extensions import TypedDict

#####################
### Agent-related ###
#####################


class HasData(Protocol):
    data: BaseModel


class Agent(ABC):
    """
    Any async `Callable`  that takes any sort of inputs and returns some object with at
    least an `data` attribute that is a `pydantic.BaseModel`.
    """

    @abstractmethod
    async def run(self, *args, **kwargs) -> HasData:
        pass


##########################
### InstructLm-related ###
##########################


class InstructLmChatRole(StrEnum):
    SYS = "system"
    USER = "user"
    ASSISTANT = "assistant"


class InstructLmMessage(TypedDict):
    role: InstructLmChatRole
    content: str


LmStreamHandler: TypeAlias = Callable[[str], Any]


class LmStreamsHandler(Protocol):
    def __call__(self, chunk_str: str, stream_idx: int | None = None):
        """
        A `Callable` that handles streaming from potentially multiple asynchronous LM streams.

        Args:
            chunk_str (str): The string chunk of LM output.
            stream_idx (int | None): When the stream is one amongst many
                asynchronous LM calls, this is the number/index of which call the stream
                chunk is coming from. Defaults to None. See `with_implicit_async_voting`.
        """
        ...


class InstructLm(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: list[InstructLmMessage],
        stream_handler: LmStreamHandler | None = None,
        **kwargs,
    ) -> str:
        pass
