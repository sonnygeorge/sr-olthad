from sr_olthad.olthad import TaskNode, TaskStatus

_example_task_in_question = TaskNode(
    task="1.3.1",
    description="Do a sub-sub-thing.",
    status=TaskStatus.IN_PROGRESS,
    retrospective=None,
    subtasks=None,
)

_example_olthad = TaskNode(
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
            retrospective="This sub-thing wasn't worth pursuing further in light of A, B, and C.",
            subtasks=None,
        ),
        TaskNode(
            task="1.3",
            description="Do this other sub-thing.",
            status=TaskStatus.IN_PROGRESS,
            retrospective=None,
            subtasks=[
                _example_task_in_question,
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

EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT = _example_task_in_question.stringify()
EXAMPLE_OLTHAD_FOR_SYS_PROMPT = _example_olthad.stringify()
