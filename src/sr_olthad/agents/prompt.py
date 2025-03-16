from sr_olthad.task_node import TaskNode, TaskStatus

_example_task_in_question = TaskNode(
    id="1.3.1",
    parent_id="1.3",
    task="Do a sub-sub-thing.",
    status=TaskStatus.IN_PROGRESS,
    retrospective=None,
)

_example_olthad = TaskNode(
    id="1",
    parent_id=None,
    task="Do a thing.",
    status=TaskStatus.IN_PROGRESS,
    retrospective=None,
    subtasks=[
        TaskNode(
            id="1.1",
            parent_id="1",
            task="Do a sub-thing.",
            status=TaskStatus.SUCCESS,
            retrospective="This sub-thing was accomplished by doing X, Y, and Z.",
        ),
        TaskNode(
            id="1.2",
            parent_id="1",
            task="Do another sub-thing.",
            status=TaskStatus.DROPPED,
            retrospective="This sub-thing wasn't worth pursuing further in light of A, B, and C.",
        ),
        TaskNode(
            id="1.3",
            parent_id="1",
            task="Do this other sub-thing.",
            status=TaskStatus.IN_PROGRESS,
            retrospective=None,
            subtasks=[
                _example_task_in_question,
                TaskNode(
                    id="1.3.2",
                    parent_id="1.3",
                    task="Do another sub-sub-thing.",
                    status=TaskStatus.PLANNED,
                    retrospective=None,
                ),
            ],
        ),
        TaskNode(
            id="1.4",
            parent_id="1",
            task="Do yet another sub-thing.",
            status=TaskStatus.PLANNED,
            retrospective=None,
        ),
    ],
)

EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT = _example_task_in_question.stringify()
EXAMPLE_OLTHAD_FOR_SYS_PROMPT = _example_olthad.stringify()
