from sr_olthad import DomainSpecificSysPromptInputData
from sr_olthad.olthad import TaskNode
from sr_olthad.schema import LmAgentName, TaskStatus, UserPromptInputData
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

SYS_PROMPT_INPUT_DATA = DomainSpecificSysPromptInputData(
    lm_role_as_verb_phrase="controls a human in a video game",
    domain_exposition="In the video game, you have access to all reasonable human controls/actions.",
)

USER_PROMPT_INPUT_DATA = UserPromptInputData(
    env_state="Only one slice remains.",
    olthad=DUMMY_ROOT_TASK_NODE.stringify(),
    task_in_question=DUMMY_TASK_IN_QUESTION.stringify(),
)


def print_backtracker_agent_prompts():
    print("\n###############################################" * 2)
    print("######### Exhaustive Effort Classifier ########")
    print("###############################################\n" * 2)

    messages = get_input_messages(
        lm_agent_name=LmAgentName.EXHAUSTIVE_EFFORT_CLF,
        user_prompt_input_data=USER_PROMPT_INPUT_DATA,
        sys_prompt_input_data=SYS_PROMPT_INPUT_DATA,
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
        user_prompt_input_data=USER_PROMPT_INPUT_DATA,
        sys_prompt_input_data=SYS_PROMPT_INPUT_DATA,
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
        user_prompt_input_data=USER_PROMPT_INPUT_DATA,
        sys_prompt_input_data=SYS_PROMPT_INPUT_DATA,
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
        user_prompt_input_data=USER_PROMPT_INPUT_DATA,
        sys_prompt_input_data=SYS_PROMPT_INPUT_DATA,
    )
    print("***********")
    print("*** SYS ***")
    print("***********\n")
    print(messages[0]["content"])
    print("\n************")
    print("*** USER ***")
    print("************\n")
    print(messages[1]["content"])


if __name__ == "__main__":
    print_backtracker_agent_prompts()
