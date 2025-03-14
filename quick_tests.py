import asyncio
import sys
from typing import Optional

import rich
from dotenv import load_dotenv
from jinja2 import Template
from loguru import logger
from pydantic import BaseModel

sys.path.append("src")

from lms import OpenAIInstructLm
from schema import (
    InstructLmAgent,
    InstructLmAgentReturn,
    InstructLmMessage,
    MultipleChoiceQuestionAgent,
    MultipleChoiceQuestionAgentOutputData,
    MultipleChoiceQuestionAgentReturn,
    LmStreamHandler,
)
from agents import SingleTurnChatAgent
from utils import implicitly_call_multiple_times_and_take_majority_vote


# TODO: use enums?

load_dotenv()


class PrintOneLmStreamHandler(LmStreamHandler):
    def __call__(self, chunk_str: str, async_call_idx: Optional[int] = None):
        # I.e. don't print more than the first of a series of async calls
        if async_call_idx is None or async_call_idx == 0:
            print(chunk_str, end="", flush=True)


def test_instruct_lm_agent_types_and_async_voting():
    class ExampleAgentInputData(BaseModel):
        pass

    class ExampleAgentOutputData(BaseModel):
        pass

    class ExampleMultipleChoiceQuestionAgent(MultipleChoiceQuestionAgent):
        multiple_choice_options = {"A", "B", "C", "D"}

        async def _call(self, input_data, stream_handler=None):
            print("Invoking ExampleMultipleChoiceQuestionAgent")
            await asyncio.sleep(0.35)
            return MultipleChoiceQuestionAgentReturn(
                output_data=MultipleChoiceQuestionAgentOutputData(
                    chosen="A", reasoning="A is best"
                ),
                messages=[{"role": "assistant", "content": "A"}],
            )

        # @implicitly_call_multiple_times_and_take_majority_vote(
        #     n_calls=9, max_async_calls=3
        # )
        async def __call__(self, input_data, **kwargs):
            call = implicitly_call_multiple_times_and_take_majority_vote(
                n_calls=9, max_async_calls=3
            )(self._call)
            return await call(self, input_data, **kwargs)

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
            stream_handler=PrintOneLmStreamHandler(),
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

    def stream_handler(chunk_str: str, async_call_num: Optional[int] = None):
        print(chunk_str, end="", flush=True)

    sum_of_numbers = asyncio.run(
        addition_agent(
            input_data=AdditionAgentInputData(first_number=2, second_number=3),
            stream_handler=stream_handler,
            max_tokens=100,
        )
    ).output_data.sum_of_numbers
    print("\n\n", sum_of_numbers)


def print_backtracker_agent_prompts():
    from sr_olthad.agents.config import BacktrackerConfig as cfg

    print("\n###############################################" * 2)
    print("######### Exhaustive Effort Classifier ########")
    print("###############################################\n" * 2)
    print("***********")
    print("*** SYS ***")
    print("***********\n")
    print(cfg.ExhaustiveEffortClfConfig.SYS_PROMPT)
    print("\n************")
    print("*** USER ***")
    print("************\n")
    print(cfg.ExhaustiveEffortClfConfig.USER_PROMPT_TEMPLATE.render())

    print("\n################################################" * 2)
    print("###### Most Worthwhile Pursuit Classifier ######")
    print("################################################\n" * 2)
    print("***********")
    print("*** SYS ***")
    print("***********\n")
    print(cfg.MostWorthwhilePursuitClfConfig.SYS_PROMPT)
    print("\n************")
    print("*** USER ***")
    print("************\n")
    print(cfg.MostWorthwhilePursuitClfConfig.USER_PROMPT_TEMPLATE.render())

    print("\n###############################################" * 2)
    print("########## Partial Success Classifier #########")
    print("###############################################\n" * 2)
    print("***********")
    print("*** SYS ***")
    print("***********\n")
    print(cfg.PartialSuccessClfConfig.SYS_PROMPT)
    print("\n************")
    print("*** USER ***")
    print("************\n")
    print(cfg.PartialSuccessClfConfig.USER_PROMPT_TEMPLATE.render())

    print("\n##############################################" * 2)
    print("###### Successful Completion Classifier ######")
    print("##############################################\n" * 2)
    print("***********")
    print("*** SYS ***")
    print("***********\n")
    print(cfg.SuccessfulCompletionClfConfig.SYS_PROMPT)
    print("\n************")
    print("*** USER ***")
    print("************\n")
    print(cfg.SuccessfulCompletionClfConfig.USER_PROMPT_TEMPLATE.render())


def test_backtracker():
    from sr_olthad.enums import TaskStatus
    from sr_olthad.agents import Backtracker, BacktrackerInputData
    from sr_olthad.olthad.task_node import TaskNode

    # env_state = "You are sitting at a wood table. The lights are on. Two slices of pizza remain."
    env_state = "It's 4:56pm. You feel full. The pizza is cold."
    task_in_question = TaskNode(
        task="1.1",
        description="Eat all four slices of the pizza.",
        status=TaskStatus.IN_PROGRESS,
        retrospective=None,
        subtasks=[
            TaskNode(
                task="1.1.1",
                description="Eat the first slice.",
                status=TaskStatus.SUCCESS,
                retrospective="You ate the first slice of pizza.",
                subtasks=None,
            ),
            TaskNode(
                task="1.1.2",
                description="Eat the second slice.",
                status=TaskStatus.SUCCESS,
                retrospective="You ate the second slice of pizza.",
                subtasks=None,
            ),
            TaskNode(
                task="1.1.3",
                description="Eat the third slice.",
                status=TaskStatus.PLANNED,
                retrospective=None,
                subtasks=None,
            ),
            TaskNode(
                task="1.1.4",
                description="Eat the fourth slice.",
                status=TaskStatus.PLANNED,
                retrospective=None,
                subtasks=None,
            ),
        ],
    )
    olthad = TaskNode(
        task="1",
        description="Satiate your hunger.",
        status=TaskStatus.IN_PROGRESS,
        retrospective=None,
        subtasks=[task_in_question],
    )

    def wait_for_user_to_proceed(messages):
        input("\n\nPress Enter to continue...")
        return

    backtracker_input_data = BacktrackerInputData(
        env_state=env_state,
        olthad=olthad,
        task_in_question=task_in_question,
    )

    backtracker = Backtracker()  # Initialize the backtracker agent w/ default configs
    return_obj = asyncio.run(
        backtracker(
            input_data=backtracker_input_data,
            stream_handler=PrintOneLmStreamHandler(),
            callback_after_each_lm_step=wait_for_user_to_proceed,
        )
    )
    print("\n\nCHOSEN STATUS:\n")
    print(return_obj.output_data.chosen_status)
    print("\nRETROSPECTIVE:\n")
    print(return_obj.output_data.retrospective)
    print("\nBACKTRACK TO:\n")
    print(return_obj.output_data.backtrack_to)


if __name__ == "__main__":
    # test_instruct_lm_agent_types_and_async_voting()
    # test_openai_instruct_lm()
    # test_single_turn_chat_agent()
    # print_backtracker_agent_prompts()
    # test_backtracker_successful_completion_clf()
    test_backtracker()
