from enum import StrEnum

from sr_olthad.enums import TaskStatus
from sr_olthad.task_node import TaskNode

# NOTE: This must align with `schema.MultipleChoiceQuestionAgentOutputData`, in order
# for LMs to know to output somethng that can be parsed with this Pydantic model.
BINARY_OUTPUT_JSON_FORMAT_SPEC = """{
    "chosen": "(str) Your answer choice",
    "reasoning": "(str) Explanation of the nuance(s) behind your choice",
}"""

EXAMPLE_TASK_IN_QUESTION = TaskNode(
    task="1.3.1",
    description="Do a sub-sub-thing.",
    status=TaskStatus.IN_PROGRESS,
    retrospective=None,
    subtasks=None,
)

EXAMPLE_OLTHAD = TaskNode(
    task="1",
    description="Do a thing.",
    status=TaskStatus.IN_PROGRESS,
    retrospective=None,
    subtasks=[
        TaskNode(
            task="1.1",
            description="Do a sub-thing.",
            status=TaskStatus.SUCCESS,
            retrospective="This sub-thing was accomplished by doing X, Y, and Z.",
            subtasks=None,
        ),
        TaskNode(
            task="1.2",
            description="Do another sub-thing.",
            status=TaskStatus.DROPPED,
            retrospective="This sub-thing wasn't worth pusuing further in light of A, B, and C.",
            subtasks=None,
        ),
        TaskNode(
            task="1.3",
            description="Do this other sub-thing.",
            status=TaskStatus.IN_PROGRESS,
            retrospective=None,
            subtasks=[
                EXAMPLE_TASK_IN_QUESTION,
                TaskNode(
                    task="1.3.2",
                    description="Do another sub-sub-thing.",
                    status=TaskStatus.PLANNED,
                    retrospective=None,
                    subtasks=None,
                ),
            ],
        ),
        TaskNode(
            task="1.4",
            description="Do yet another sub-thing.",
            status=TaskStatus.PLANNED,
            retrospective=None,
            subtasks=None,
        ),
    ],
)


class SysPromptInsertionField(StrEnum):
    OLTHAD_EXAMPLE = "olthad_example"
    TASK_IN_QUESTION_EXAMPLE = "task_in_question_example"
    BINARY_OUTPUT_JSON_FORMAT_SPEC = "output_json_format"


SYS_PROMPT_INSERTIONS_REGISTRY = {
    SysPromptInsertionField.OLTHAD_EXAMPLE: str(EXAMPLE_OLTHAD),
    SysPromptInsertionField.TASK_IN_QUESTION_EXAMPLE: str(EXAMPLE_TASK_IN_QUESTION),
    SysPromptInsertionField.BINARY_OUTPUT_JSON_FORMAT_SPEC: BINARY_OUTPUT_JSON_FORMAT_SPEC,
}
