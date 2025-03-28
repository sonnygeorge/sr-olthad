import sys

from dotenv import load_dotenv

sys.path.append("src")

load_dotenv()

from sr_olthad.olthad import TaskNode
from sr_olthad.schema import CommonUserPromptInputData, LmAgentName, TaskStatus
from sr_olthad.utils import get_input_messages

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

DUMMY_ENV_STATE = "Only one slice remains."


def dummy_get_domain_specific_insert(_, __):
    return "You are a human in a video game."


def print_backtracker_agent_prompts():
    prompt_input_data = CommonUserPromptInputData(
        env_state=DUMMY_ENV_STATE,
        olthad=DUMMY_ROOT_TASK_NODE.stringify(),
        task_in_question=DUMMY_TASK_IN_QUESTION.stringify(),
    )

    print("\n###############################################" * 2)
    print("######### Exhaustive Effort Classifier ########")
    print("###############################################\n" * 2)

    messages = get_input_messages(
        lm_agent_name=LmAgentName.EXHAUSTIVE_EFFORT_CLF,
        user_prompt_input_data=prompt_input_data,
        get_domain_specific_insert=dummy_get_domain_specific_insert,
    )
    print("***********")
    print("*** SYS ***")
    print("***********\n")
    print(messages[0]["content"])
    print("\n************")
    print("*** USER ***")
    print("************\n")
    print(messages[1]["content"])

    print("\n################################################" * 2)
    print("###### Most Worthwhile Pursuit Classifier ######")
    print("################################################\n" * 2)

    messages = get_input_messages(
        lm_agent_name=LmAgentName.MOST_WORTHWHILE_PURSUIT_CLF,
        user_prompt_input_data=prompt_input_data,
        get_domain_specific_insert=dummy_get_domain_specific_insert,
    )
    print("***********")
    print("*** SYS ***")
    print("***********\n")
    print(messages[0]["content"])
    print("\n************")
    print("*** USER ***")
    print("************\n")
    print(messages[1]["content"])

    print("\n###############################################" * 2)
    print("########## Partial Success Classifier #########")
    print("###############################################\n" * 2)

    messages = get_input_messages(
        lm_agent_name=LmAgentName.PARTIAL_SUCCESS_CLF,
        user_prompt_input_data=prompt_input_data,
        get_domain_specific_insert=dummy_get_domain_specific_insert,
    )
    print("***********")
    print("*** SYS ***")
    print("***********\n")
    print(messages[0]["content"])
    print("\n************")
    print("*** USER ***")
    print("************\n")
    print(messages[1]["content"])

    print("\n##############################################" * 2)
    print("###### Successful Completion Classifier ######")
    print("##############################################\n" * 2)

    messages = get_input_messages(
        lm_agent_name=LmAgentName.SUCCESSFUL_COMPLETION_CLF,
        user_prompt_input_data=prompt_input_data,
        get_domain_specific_insert=dummy_get_domain_specific_insert,
    )
    print("***********")
    print("*** SYS ***")
    print("***********\n")
    print(messages[0]["content"])
    print("\n************")
    print("*** USER ***")
    print("************\n")
    print(messages[1]["content"])


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
#     def __call__(self, chunk_str: str, async_call_idx: int | None = None):
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
    print_backtracker_agent_prompts()
    # test_obfuscate_and_redact_in_stringification()
