import asyncio
import sys
from typing import Optional

from dotenv import load_dotenv

sys.path.append("src")

from agent_framework.schema import LmStreamsHandler
from sr_olthad.emissions import PostLmGenerationStepEmission

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


def test_get_approval_before_update_generators():
    from sr_olthad.olthad import TaskNode, TaskStatus

    task_in_question = TaskNode(
        id="1.1",
        parent_id="1",
        task="Eat all four slices of the pizza.",
        status=TaskStatus.IN_PROGRESS,
        retrospective=None,
        _non_planned_subtasks=[
            TaskNode(
                id="1.1.1",
                parent_id="1.1",
                task="Eat the first slice.",
                status=TaskStatus.SUCCESS,
                retrospective="You ate the first slice of pizza.",
            ),
            TaskNode(
                id="1.1.2",
                parent_id="1.1",
                task="Eat the second slice.",
                status=TaskStatus.SUCCESS,
                retrospective="You ate the second slice of pizza.",
            ),
            TaskNode(
                id="1.1.3",
                parent_id="1.1",
                task="Eat the third slice.",
                status=TaskStatus.IN_PROGRESS,
                retrospective=None,
            ),
        ],
        _planned_subtasks=[
            TaskNode(
                id="1.1.4",
                parent_id="1.1",
                task="Eat the fourth slice.",
                status=TaskStatus.PLANNED,
                retrospective=None,
            ),
        ],
    )
    olthad = TaskNode(
        id="1",
        parent_id=None,
        task="Satiate your hunger.",
        status=TaskStatus.IN_PROGRESS,
        retrospective=None,
        _non_planned_subtasks=[task_in_question],
    )

    # First, let's test stringify with obfuscate status and redact planned subtasks
    print("\n##############################################" * 2)
    print("######### Obfuscate Status and Redact ########")
    print("##############################################\n" * 2)
    print(
        olthad.stringify(
            obfuscate_status_of=task_in_question.id,
            redact_planned_subtasks_below=task_in_question.id,
        )
    )

    # Now let's test updating planned subtasks

    print("\n##############################################" * 2)
    print("##### Diff Before Update Planned Subtasks ####")
    print("##############################################\n" * 2)

    new_planned_subtasks = [
        TaskNode(
            id="1.1.4",
            parent_id="1.1",
            task="Shove the fourth slice down the ol' gullet.",
            status=TaskStatus.PLANNED,
            retrospective="You ate the fourth slice of pizza.",
        )
    ]
    update_after_approval_decision = task_in_question.update_planned_subtasks(
        new_planned_subtasks,
        should_yield_diff_and_receive_approval_before_update=True,
        diff_root_node=olthad,
    )
    diff_lines = next(update_after_approval_decision)
    print("".join(diff_lines))

    print("\n##############################################" * 2)
    print("#### String After Update Planned Subtasks ####")
    print("##############################################\n" * 2)

    update_after_approval_decision.send(True)
    print(olthad.stringify())

    print("\n##############################################" * 2)
    print("### Diff Before Update Status+Retrospective ##")
    print("##############################################\n" * 2)

    # Now let's test updating status and retrospective
    update_after_approval_decision = (
        olthad.update_status_and_retrospective_of_in_progress_subtask(
            new_status=TaskStatus.SUCCESS,
            new_retrospective="All four slices of pizza were eaten.",
            should_yield_diff_and_receive_approval_before_update=True,
            diff_root_node=olthad,
        )
    )
    diff_lines = next(update_after_approval_decision)
    print("".join(diff_lines))

    print("\n##############################################" * 2)
    print("## String After Update Status+Retrospective ##")
    print("##############################################\n" * 2)

    update_after_approval_decision.send(True)
    print(olthad.stringify())


class PrintOneLmStreamsHandler(LmStreamsHandler):
    def __call__(self, chunk_str: str, async_call_idx: Optional[int] = None):
        # I.e. don't print more than the first of a series of async calls
        if async_call_idx is None or async_call_idx == 0:
            print(chunk_str, end="", flush=True)


def get_approval_from_user(
    emission: PostLmGenerationStepEmission,
) -> bool:
    print("\n\nDIFF:\n")
    print("".join(emission.diff_lines))
    user_input = input("\n\nApprove the update? (y/n): ")
    return user_input.lower() == "y"


def test_backtracker():
    from sr_olthad.agents import Backtracker, BacktrackerInputData
    from sr_olthad.olthad import TaskNode, TaskStatus

    # env_state = "You are sitting at a wood table. Two slices of pizza remain."
    env_state = "It's 4:56pm. You feel full. The pizza is cold."
    task_in_question = TaskNode(
        id="1.1",
        parent_id="1",
        task="Eat all four slices of the pizza.",
        status=TaskStatus.IN_PROGRESS,
        retrospective=None,
        _non_planned_subtasks=[
            TaskNode(
                id="1.1.1",
                parent_id="1.1",
                task="Eat the first slice.",
                status=TaskStatus.SUCCESS,
                retrospective="You ate the first slice of pizza.",
            ),
            TaskNode(
                id="1.1.2",
                parent_id="1.1",
                task="Eat the second slice.",
                status=TaskStatus.SUCCESS,
                retrospective="You ate the second slice of pizza.",
            ),
            TaskNode(
                id="1.1.3",
                parent_id="1.1",
                task="Eat the third slice.",
                status=TaskStatus.IN_PROGRESS,
                retrospective=None,
            ),
        ],
        _planned_subtasks=[
            TaskNode(
                id="1.1.4",
                parent_id="1.1",
                task="Eat the fourth slice.",
                status=TaskStatus.PLANNED,
                retrospective=None,
            ),
        ],
    )
    olthad = TaskNode(
        id="1",
        parent_id=None,
        task="Satiate your hunger.",
        status=TaskStatus.IN_PROGRESS,
        retrospective=None,
        _non_planned_subtasks=[task_in_question],
    )

    backtracker_input_data = BacktrackerInputData(
        env_state=env_state,
        root_task_node=olthad,
        current_task_node=task_in_question,
    )

    backtracker = Backtracker(
        streams_handler=PrintOneLmStreamsHandler(),
        callback_after_lm_generation_steps=get_approval_from_user,
    )
    return_obj = asyncio.run(
        backtracker(
            input_data=backtracker_input_data,
        )
    )
    print("\n\nCHOSEN STATUS:\n")
    print(return_obj.output_data.backtracked_from_status_to_assign)
    print("\nRETROSPECTIVE:\n")
    print(return_obj.output_data.retrospective_to_assign)
    print("\nBACKTRACK TO:\n")
    print(return_obj.output_data.id_of_ancestor_to_backtrack_to)


def test_sr_olthad():
    import random

    from sr_olthad import SrOlthad

    # from sr_olthad.olthad import TaskNode, TaskStatus

    sr_olthad = SrOlthad(
        highest_level_task="Acquire diamonds",
        domain_documentation="Single player minecraft world in peaceful mode.",
        classify_if_task_is_executable_action=lambda _: random.random() < 0.67,
        # streams_handler=PrintOneLmStreamsHandler(),
        pre_lm_generation_step_handler=print,
        post_lm_generation_step_handler=get_approval_from_user,
    )

    # Monkey patch some stuff
    sr_olthad.has_been_called_at_least_once_before = True
    # subtask_to_patch = TaskNode(
    #     id="1.1",
    #     parent_id=None,
    #     task="Find a tree.",
    #     status=TaskStatus.IN_PROGRESS,
    #     retrospective=None,
    # )
    # sr_olthad.traversal.root_node._non_planned_subtasks = [subtask_to_patch]

    # env_state = "You are standing with a tree right in front of you. You have nothing in your inventory. An appealing village with a blacksmith is visible to the north."
    # env_state = "You spawn in a flatworld where no diamonds spawn and structures have been disabled."
    env_state = "You're outside in a plains village. YOU HAVE DIAMONDS IN YOUR INVENTORY"

    while True:
        next_action = asyncio.run(
            sr_olthad(
                env_state=env_state,
            )
        )
        print("\n\nNEXT ACTION:\n")
        print(next_action)
        if next_action is None:
            break

        env_state = input("\n\nEnter the resulting environment state: ")
        # You're outside in a plains village. Inventory: {"apple": 3, "bread": 12, "iron_axe":, 1, “leather_boots”: 1, “bed”: 5, “crafting_table”: 1, “chest”: 1, "wheat": 18, "oak_sapling": 2}


if __name__ == "__main__":
    # print_backtracker_agent_prompts()
    # test_get_approval_before_update_generators()
    # test_backtracker()
    test_sr_olthad()
