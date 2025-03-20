import logging
from typing import Generic, List, Optional, Tuple, Type, TypeVar

from pydantic import BaseModel, ValidationError

from agent_framework.schema import (
    Agent,
    InstructLm,
    InstructLmChatRole,
    InstructLmMessage,
    LmStreamHandler,
    PotentiallyNestedInstructLmMessages,
)
from agent_framework.utils import detect_extract_and_parse_json_from_text, with_retry

BaseModelT = TypeVar("OutputDataT", bound=BaseModel)


class SingleTurnChatAgentReturn(BaseModel, Generic[BaseModelT]):
    output_data: BaseModelT
    # NOTE: Whenever an agent is potentially wrapped w/ `with_implicit_async_voting`
    # decorator, attributes of the return object as well as the `output_data` attribute
    # should be thought of as potentially nested.
    # This is weird, but I didn't want to rewrite voting logic over and over again so my
    # idea was that decorator.
    messages: PotentiallyNestedInstructLmMessages


class InstructLmChatAgent(Agent, Generic[BaseModelT]):
    """
    An agent that queries an instruct LM with input messages and automatically parses the
    LM response using the specified `response_json_data_model` Pydantic model.
    """

    def __init__(  # TODO: Docstring
        self,
        instruct_lm: InstructLm,
        response_json_data_model: Type[BaseModelT],
        max_tries_to_get_valid_response: int = 1,
        logger: Optional[logging.Logger] = None,
    ):
        self.instruct_lm = instruct_lm
        self.output_data_model = response_json_data_model
        self.logger = logger
        # Wrap `self._get_valid_response` with retry decorator
        self._get_response_and_parse = with_retry(
            # TODO: Update exceptions to be more precise
            permissible_exceptions=(ValidationError, ValueError, Exception),
            max_tries=max_tries_to_get_valid_response,
            logger=self.logger,
        )(self._get_response_and_parse)

    async def _get_response_and_parse(
        self,
        input_messages: List[InstructLmMessage],
        stream_handler: Optional[LmStreamHandler] = None,
        **kwargs,  # kwargs passed through to the InstructLm.generate method
    ) -> Tuple[BaseModelT, str]:
        response = await self.instruct_lm.generate(
            messages=input_messages, stream_handler=stream_handler, **kwargs
        )
        output_data = detect_extract_and_parse_json_from_text(
            text=response, model_to_extract=self.output_data_model
        )
        return output_data, response

    async def __call__(  # TODO: Docstring
        self,
        input_messages: List[InstructLmMessage],
        stream_handler: Optional[LmStreamHandler] = None,
        **kwargs,  # kwargs passed through to the InstructLm.generate method
    ) -> SingleTurnChatAgentReturn[BaseModelT]:
        output_data, response = await self._get_response_and_parse(
            input_messages=input_messages,
            stream_handler=stream_handler,
            **kwargs,
        )
        assistant_message = InstructLmMessage(
            role=InstructLmChatRole.ASSISTANT, content=response
        )
        return SingleTurnChatAgentReturn(
            output_data=output_data,
            messages=input_messages + [assistant_message],
        )
