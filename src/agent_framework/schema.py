from abc import ABC, abstractmethod
from enum import StrEnum
from typing import List, Optional, Protocol, TypedDict

from pydantic import BaseModel


class InstructLmChatRole(StrEnum):
    SYS = "system"
    USER = "user"
    ASSISTANT = "assistant"


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


class HasOutputData(Protocol):
    output_data: BaseModel


class HasMessages(Protocol):
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class HasOutputDataAndMessages(HasOutputData, HasMessages):
    pass


class Agent(ABC):
    """
    Any async `Callable`  that takes any sort of inputs and returns some object with at
    least an `output_data` attribute that is a `pydantic.BaseModel`.
    """

    @abstractmethod
    async def __call__(self, *args, **kwargs) -> HasOutputData:
        pass
