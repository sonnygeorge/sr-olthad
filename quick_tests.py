import asyncio
import sys

import rich
from dotenv import load_dotenv
from pydantic import BaseModel

sys.path.append("src")

from instruct_lms import OpenAIInstructLm
from types_and_models import (
    InstructLmAgent,
    InstructLmAgentReturn,
    InstructLmMessage,
    MultipleChoiceQuestionAgent,
    MultipleChoiceQuestionAgentOutputData,
    MultipleChoiceQuestionAgentReturn,
)
from utils import implicitly_call_multiple_times_and_take_majority_vote


load_dotenv()


def test_instruct_lm_agent_types_and_async_voting():
    class ExampleAgentInputData(BaseModel):
        pass

    class ExampleAgentOutputData(BaseModel):
        pass

    class ExampleMultipleChoiceQuestionAgent(MultipleChoiceQuestionAgent):
        multiple_choice_options = {"A", "B", "C", "D"}

        @implicitly_call_multiple_times_and_take_majority_vote(
            num_calls=9, max_async_calls=3
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
    lm = OpenAIInstructLm()
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


if __name__ == "__main__":
    # test_instruct_lm_agent_types_and_async_voting()
    test_openai_instruct_lm()
