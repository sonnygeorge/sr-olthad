import logging
from typing import Any, Callable, Generic, List, Optional, Type, TypeVar

from jinja2 import Template
from pydantic import BaseModel, ValidationError

from enums import InstructLmChatRole
from schema import (
    InstructLm,
    InstructLmAgent,
    InstructLmMessage,
    InstructLmAgentReturn,
    MultipleChoiceQuestionAgent,
    MultipleChoiceQuestionAgentOutputData,
    MultipleChoiceQuestionAgentReturn,
)
from utils import detect_extract_and_parse_json_from_text, with_retry


InputDataT = TypeVar("InputDataT", bound=BaseModel)
OutputDataT = TypeVar("OutputDataT", bound=BaseModel)


class SingleTurnChatAgentReturn(InstructLmAgentReturn, Generic[OutputDataT]):
    output_data: OutputDataT
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class SingleTurnChatAgent(InstructLmAgent, Generic[InputDataT, OutputDataT]):
    """An agent that queries an instruct LM with a user prompt and (optional) system
    prompt (automatically parsing the output data model for the return object).

    Example:
        ```python
        class AdditionAgentInputData(BaseModel):
            first_number: int
            second_number: int

        class AdditionAgentOutputData(BaseModel):
            sum_of_numbers: int

        sys_prompt = '''You are a helpful assistant that adds numbers.
        Give your answer in this JSON format: {"sum_of_numbers": (int)}.'''

        # Adding this type hint allows type-checkers to know the input/output data types
        addition_agent: SingleTurnChatAgent[AdditionAgentInputData, AdditionAgentOutputData] = (
            SingleTurnChatAgent(
                ...,  # Other stuff
                sys_prompt=sys_prompt,
                user_prompt_template=Template("Add {first_number} and {second_number}."),
                input_data_model=AdditionAgentInputData,
                output_data_model=AdditionAgentOutputData,
            )
        )

        sum_of_numbers = addition_agent(
            AdditionAgentInputData(first_number=2, second_number=3)
        ).output_data.sum_of_numbers
    """

    def __init__(
        self,
        instruct_lm: InstructLm,
        input_data_model: Type[InputDataT],
        output_data_model: Type[OutputDataT],
        user_prompt_template: Template,
        sys_prompt: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        self.instruct_lm = instruct_lm
        self.input_data_model = input_data_model
        self.output_data_model = output_data_model
        self.sys_prompt = sys_prompt
        self.user_prompt_template = user_prompt_template
        self.logger = logger

    def _prepare_messages(self, input_data: InputDataT) -> List[InstructLmMessage]:
        user_prompt = self.user_prompt_template.render(**input_data.model_dump())
        messages = [
            InstructLmMessage(role=InstructLmChatRole.SYS, content=self.sys_prompt),
            InstructLmMessage(role=InstructLmChatRole.USER, content=user_prompt),
        ]
        if self.sys_prompt is None:
            messages.pop(0)
        return messages

    async def _get_valid_response(
        self,
        messages: List[InstructLmMessage],
        stream_handler: Optional[Callable[[str], Any]] = None,
        **kwargs,
    ) -> OutputDataT:
        response = await self.instruct_lm.generate(
            messages=messages, stream_handler=stream_handler, **kwargs
        )
        return detect_extract_and_parse_json_from_text(
            text=response, model_to_extract=self.output_data_model
        )

    async def __call__(
        self,
        input_data: InputDataT,
        n_tries_to_get_valid_response: int = 1,
        stream_handler: Optional[Callable[[str], Any]] = None,
        **kwargs,  # kwargs for the InstructLm.generate method
    ) -> SingleTurnChatAgentReturn[OutputDataT]:
        messages = self._prepare_messages(input_data=input_data)
        # Wrap the `_get_valid_response` method with retry logic
        get_valid_response_with_retry = with_retry(
            # TODO: Update expections to be more precise
            permissible_exceptions=(ValidationError, ValueError, Exception),
            max_tries=n_tries_to_get_valid_response,
            logger=self.logger,
        )(self._get_valid_response)
        output_data = await get_valid_response_with_retry(
            messages=messages, stream_handler=stream_handler, **kwargs
        )
        return SingleTurnChatAgentReturn(output_data=output_data, messages=messages)


class SingleTurnChatMultipleChoiceAgent(
    SingleTurnChatAgent[InputDataT, MultipleChoiceQuestionAgentOutputData],
    MultipleChoiceQuestionAgent,
):
    """Multiple-choice variant of a `SingleTurnChatAgent`"""

    multiple_choice_options: List[str]

    def __init__(
        self,
        multiple_choice_options: List[str],
        instruct_lm: InstructLm,
        input_data_model: Type[InputDataT],
        user_prompt_template: Template,
        sys_prompt: Optional[str] = None,
        logger: Optional[logging.Logger] = None,
    ):
        super().__init__(
            instruct_lm=instruct_lm,
            input_data_model=input_data_model,
            output_data_model=MultipleChoiceQuestionAgentOutputData,
            user_prompt_template=user_prompt_template,
            sys_prompt=sys_prompt,
            logger=logger,
        )
        self.multiple_choice_options = multiple_choice_options

    async def __call__(
        self,
        input_data: InputDataT,
        n_tries_to_get_valid_response: int = 1,
        stream_handler: Optional[Callable[[str], Any]] = None,
        **kwargs,  # kwargs for the InstructLm.generate method
    ) -> MultipleChoiceQuestionAgentReturn:
        return await super().__call__(
            input_data=input_data,
            n_tries_to_get_valid_response=n_tries_to_get_valid_response,
            stream_handler=stream_handler,
            **kwargs,
        )
