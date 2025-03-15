import asyncio
import sys
from typing import Optional

from dotenv import load_dotenv

sys.path.append("src")

from agent_framework.schema import LmStreamHandler

load_dotenv()


def print_backtracker_agent_prompts():
    from sr_olthad.agents.backtracker.prompt import (
        EXHAUSTIVE_EFFORT_CLF_PROMPT_REGISTRY,
        MOST_WORTHWHILE_PURSUIT_CLF_PROMPT_REGISTRY,
        PARTIAL_SUCCESS_CLF_PROMPT_REGISTRY,
        SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY,
    )
    from sr_olthad.config import BacktrackerCfg as cfg

    exhaustive_effort_prompts = EXHAUSTIVE_EFFORT_CLF_PROMPT_REGISTRY[
        cfg.ExhaustiveEffortClf.PROMPTS_VERSION
    ]
    most_worthwhile_pursuit_prompts = (
        MOST_WORTHWHILE_PURSUIT_CLF_PROMPT_REGISTRY[
            cfg.MostWorthwhilePursuitClfCfg.PROMPTS_VERSION
        ]
    )
    partial_success_prompts = PARTIAL_SUCCESS_CLF_PROMPT_REGISTRY[
        cfg.PartialSuccessClfCfg.PROMPTS_VERSION
    ]
    successful_completion_prompts = SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY[
        cfg.SuccessfulCompletionClfCfg.PROMPTS_VERSION
    ]

    print("\n###############################################" * 2)
    print("######### Exhaustive Effort Classifier ########")
    print("###############################################\n" * 2)
    print("***********")
    print("*** SYS ***")
    print("***********\n")
    print(exhaustive_effort_prompts.sys_prompt_template.render())
    print("\n************")
    print("*** USER ***")
    print("************\n")
    print(exhaustive_effort_prompts.user_prompt_template.render())

    print("\n################################################" * 2)
    print("###### Most Worthwhile Pursuit Classifier ######")
    print("################################################\n" * 2)
    print("***********")
    print("*** SYS ***")
    print("***********\n")
    print(most_worthwhile_pursuit_prompts.sys_prompt_template.render())
    print("\n************")
    print("*** USER ***")
    print("************\n")
    print(most_worthwhile_pursuit_prompts.user_prompt_template.render())

    print("\n###############################################" * 2)
    print("########## Partial Success Classifier #########")
    print("###############################################\n" * 2)
    print("***********")
    print("*** SYS ***")
    print("***********\n")
    print(partial_success_prompts.sys_prompt_template.render())
    print("\n************")
    print("*** USER ***")
    print("************\n")
    print(partial_success_prompts.user_prompt_template.render())

    print("\n##############################################" * 2)
    print("###### Successful Completion Classifier ######")
    print("##############################################\n" * 2)
    print("***********")
    print("*** SYS ***")
    print("***********\n")
    print(successful_completion_prompts.sys_prompt_template.render())
    print("\n************")
    print("*** USER ***")
    print("************\n")
    print(successful_completion_prompts.user_prompt_template.render())


class PrintOneLmStreamHandler(LmStreamHandler):
    def __call__(self, chunk_str: str, async_call_idx: Optional[int] = None):
        # I.e. don't print more than the first of a series of async calls
        if async_call_idx is None or async_call_idx == 0:
            print(chunk_str, end="", flush=True)


def test_backtracker():
    from sr_olthad.agents import Backtracker, BacktrackerInputData
    from sr_olthad.olthad import TaskNode, TaskStatus

    # env_state = "You are sitting at a wood table. Two slices of pizza remain."
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
        olthad_root=olthad,
        task_in_question=task_in_question,
    )

    backtracker = (
        Backtracker()
    )  # Initialize the backtracker agent w/ default configs
    return_obj = asyncio.run(
        backtracker(
            input_data=backtracker_input_data,
            stream_handler=PrintOneLmStreamHandler(),
            callback_after_each_lm_step=wait_for_user_to_proceed,
        )
    )
    print("\n\nCHOSEN STATUS:\n")
    print(return_obj.output_data.status_to_assign)
    print("\nRETROSPECTIVE:\n")
    print(return_obj.output_data.retrospective)
    print("\nBACKTRACK TO:\n")
    print(return_obj.output_data.ancestor_to_backtrack_to_if_not_parent)


if __name__ == "__main__":
    # print_backtracker_agent_prompts()
    test_backtracker()
