import logging
from typing import Generic, List, Optional, Type, TypeVar

from jinja2 import Template
from pydantic import BaseModel, ValidationError

from agent_framework.schema import (
    Agent,
    InstructLm,
    InstructLmChatRole,
    InstructLmMessage,
    LmStreamHandler,
)
from agent_framework.utils import (
    detect_extract_and_parse_json_from_text,
    with_retry,
)

BaseModelT = TypeVar("OutputDataT", bound=BaseModel)


class SingleTurnChatAgentReturn(BaseModel, Generic[BaseModelT]):
    output_data: BaseModelT
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class SingleTurnChatAgent(Agent, Generic[BaseModelT]):
    """
    An agent that: (1) renders a prompt with the data fields of a Pydantic model,
    (2) queries an instruct LM with the resulting user prompt and an (optional) system
    prompt, and (3) automatically parses the LM response with the specified
    `response_json_data_model` Pydantic model.
    """

    def __init__(  # TODO: Docstring
        self,
        instruct_lm: InstructLm,
        response_json_data_model: Type[BaseModelT],
        user_prompt_template: Template,
        sys_prompt: Optional[str] = None,
        max_tries_to_get_valid_response: int = 1,
        logger: Optional[logging.Logger] = None,
    ):
        self.instruct_lm = instruct_lm
        self.output_data_model = response_json_data_model
        self.sys_prompt = sys_prompt
        self.user_prompt_template = user_prompt_template
        self.logger = logger
        # Wrap `self._get_valid_response` with retry decorator
        self._get_valid_response = with_retry(
            # TODO: Update exceptions to be more precise
            permissible_exceptions=(ValidationError, ValueError, Exception),
            max_tries=max_tries_to_get_valid_response,
            logger=self.logger,
        )(self._get_valid_response)

    def _prepare_messages(
        self, input_data: BaseModel
    ) -> List[InstructLmMessage]:
        # TODO: Raise error if model and template fields don't match up
        input_data = {k: str(v) for k, v in input_data.__dict__.items()}
        user_prompt = self.user_prompt_template.render(**input_data)
        messages = [
            InstructLmMessage(
                role=InstructLmChatRole.SYS, content=self.sys_prompt
            ),
            InstructLmMessage(
                role=InstructLmChatRole.USER, content=user_prompt
            ),
        ]
        if self.sys_prompt is None:
            messages.pop(0)
        return messages

    async def _get_valid_response(
        self,
        messages: List[InstructLmMessage],
        stream_handler: Optional[LmStreamHandler] = None,
        **kwargs,  # kwargs passed through to the InstructLm.generate method
    ) -> BaseModelT:
        response = await self.instruct_lm.generate(
            messages=messages, stream_handler=stream_handler, **kwargs
        )
        return detect_extract_and_parse_json_from_text(
            text=response, model_to_extract=self.output_data_model
        )

    async def __call__(  # TODO: Docstring
        self,
        prompt_template_data: BaseModel,
        stream_handler: Optional[LmStreamHandler] = None,
        **kwargs,  # kwargs passed through to the InstructLm.generate method
    ) -> SingleTurnChatAgentReturn[BaseModelT]:
        messages = self._prepare_messages(input_data=prompt_template_data)
        output_data = await self._get_valid_response(
            messages=messages, stream_handler=stream_handler, **kwargs
        )
        return SingleTurnChatAgentReturn(
            output_data=output_data, messages=messages
        )
