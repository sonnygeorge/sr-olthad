import sys

from dotenv import load_dotenv

sys.path.append("src")

from sr_olthad.olthad import TaskNode, TaskStatus

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
    most_worthwhile_pursuit_prompts = MOST_WORTHWHILE_PURSUIT_CLF_PROMPT_REGISTRY[
        cfg.MostWorthwhilePursuitClfCfg.PROMPTS_VERSION
    ]
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


DUMMY_TASK_IN_QUESTION = TaskNode(
    _id="1.1",
    _parent_id="1",
    _task="Eat all four slices of the pizza.",
    _status=TaskStatus.IN_PROGRESS,
    _retrospective=None,
    _non_planned_subtasks=[
        TaskNode(
            _id="1.1.1",
            _parent_id="1.1",
            _task="Eat the first slice.",
            _status=TaskStatus.SUCCESS,
            _retrospective="You ate the first slice of pizza.",
        ),
        TaskNode(
            _id="1.1.2",
            _parent_id="1.1",
            _task="Eat the second slice.",
            _status=TaskStatus.SUCCESS,
            _retrospective="You ate the second slice of pizza.",
        ),
        TaskNode(
            _id="1.1.3",
            _parent_id="1.1",
            _task="Eat the third slice.",
            _status=TaskStatus.IN_PROGRESS,
            _retrospective=None,
        ),
    ],
    _planned_subtasks=[
        TaskNode(
            _id="1.1.4",
            _parent_id="1.1",
            _task="Eat the fourth slice.",
            _status=TaskStatus.PLANNED,
            _retrospective=None,
        ),
    ],
)
DUMMY_ROOT_TASK_NODE = TaskNode(
    _id="1",
    _parent_id=None,
    _task="Satiate your hunger.",
    _status=TaskStatus.IN_PROGRESS,
    _retrospective=None,
    _non_planned_subtasks=[DUMMY_TASK_IN_QUESTION],
)


def test_obfuscate_and_redact_in_stringification():
    # First, let's test stringify with obfuscate status and redact planned subtasks
    print("\n##############################################" * 2)
    print("######### Obfuscate Status and Redact ########")
    print("##############################################\n" * 2)
    print(
        DUMMY_ROOT_TASK_NODE.stringify(
            obfuscate_status_of=DUMMY_TASK_IN_QUESTION._id,
            redact_planned_subtasks_below=DUMMY_TASK_IN_QUESTION._id,
        )
    )


# class PrintOneLmStreamsHandler(LmStreamsHandler):
#     def __call__(self, chunk_str: str, async_call_idx: Optional[int] = None):
#         # I.e. don't print more than the first of a series of async calls
#         if async_call_idx is None or async_call_idx == 0:
#             print(chunk_str, end="", flush=True)


# def get_approval_from_user(
#     emission: PostLmGenerationStepEmission,
# ) -> bool:
#     print("\n\nDIFF:\n")
#     print("".join(emission.diff))
#     user_input = input("\n\nApprove the update? (y/n): ")
#     return user_input.lower() == "y"


if __name__ == "__main__":
    # print_backtracker_agent_prompts()
    test_obfuscate_and_redact_in_stringification()
