import asyncio
import sys

import rich
from dotenv import load_dotenv
from jinja2 import Template
from loguru import logger
from pydantic import BaseModel

sys.path.append("src")

from instruct_lms import OpenAIInstructLm
from schema import (
    InstructLmAgent,
    InstructLmAgentReturn,
    InstructLmMessage,
    MultipleChoiceQuestionAgent,
    MultipleChoiceQuestionAgentOutputData,
    MultipleChoiceQuestionAgentReturn,
)
from single_turn_chat_agent import SingleTurnChatAgent
from utils import implicitly_call_multiple_times_and_take_majority_vote


# TODO: use enums?

load_dotenv()


def test_instruct_lm_agent_types_and_async_voting():
    class ExampleAgentInputData(BaseModel):
        pass

    class ExampleAgentOutputData(BaseModel):
        pass

    class ExampleMultipleChoiceQuestionAgent(MultipleChoiceQuestionAgent):
        multiple_choice_options = {"A", "B", "C", "D"}

        @implicitly_call_multiple_times_and_take_majority_vote(
            n_calls=9, max_async_calls=3
        )
        async def __call__(self, input_data, **kwargs):
            print("Invoking ExampleMultipleChoiceQuestionAgent")
            await asyncio.sleep(0.5)  # Simulate async work
            return MultipleChoiceQuestionAgentReturn(
                output_data=MultipleChoiceQuestionAgentOutputData(
                    chosen="A", reasoning="A is best"
                ),
                messages=[{"role": "assistant", "content": "A"}],
            )

    class ExampleInstructLmAgent(InstructLmAgent):
        async def __call__(
            self, input_data: ExampleAgentInputData, **kwargs
        ) -> InstructLmAgentReturn:
            return InstructLmAgentReturn(
                output_data=ExampleAgentOutputData(),
                messages=[],
            )

    agent = ExampleInstructLmAgent()
    return_obj = asyncio.run(agent(ExampleAgentInputData()))
    rich.print(return_obj)

    agent = ExampleMultipleChoiceQuestionAgent()
    return_obj = asyncio.run(agent(ExampleAgentInputData()))
    rich.print(return_obj.output_data.reasoning)


def test_openai_instruct_lm():
    lm = OpenAIInstructLm(model="gpt-3.5-turbo")
    messages = [
        InstructLmMessage(role="system", content="You are a helpful assistant."),
        InstructLmMessage(role="user", content="What is the meaning of life?"),
    ]

    # Test with stream handler
    response = asyncio.run(
        lm.generate(
            messages,
            stream_handler=lambda s: print(s, end="", flush=True),
            max_tokens=15,
        )
    )

    print("\n\n")

    # Test without stream handler
    response = asyncio.run(lm.generate(messages, max_tokens=15))
    print(response)


def test_single_turn_chat_agent():
    class AdditionAgentInputData(BaseModel):
        first_number: int
        second_number: int

    class AdditionAgentOutputData(BaseModel):
        sum_of_numbers: int

    sys_prompt = """You are a helpful assistant that adds numbers.
    Give your answer in this JSON format: {"sum_of_numbers": (int)}."""

    # Adding this type hint allows type-checkers to know the input/output data types
    addition_agent: SingleTurnChatAgent[
        AdditionAgentInputData, AdditionAgentOutputData
    ] = SingleTurnChatAgent(
        instruct_lm=OpenAIInstructLm(model="gpt-3.5-turbo"),
        sys_prompt=sys_prompt,
        user_prompt_template=Template("Add {first_number} and {second_number}."),
        input_data_model=AdditionAgentInputData,
        output_data_model=AdditionAgentOutputData,
        max_tries_to_get_valid_response=3,
        logger=logger,
    )

    sum_of_numbers = asyncio.run(
        addition_agent(
            input_data=AdditionAgentInputData(first_number=2, second_number=3),
            stream_handler=lambda s: print(s, end="", flush=True),
            max_tokens=100,
        )
    ).output_data.sum_of_numbers
    print("\n\n", sum_of_numbers)


def print_most_worthwhile_pursuit_prompts():
    from sr_olthad.agents.config import BacktrackerConfig as cfg

    print(cfg.MostWorthwhilePursuitClfConfig.SYS_PROMPT)
    print(cfg.MostWorthwhilePursuitClfConfig.USER_PROMPT_TEMPLATE.render())


if __name__ == "__main__":
    # test_instruct_lm_agent_types_and_async_voting()
    # test_openai_instruct_lm()
    # test_single_turn_chat_agent()
    print_most_worthwhile_pursuit_prompts()
