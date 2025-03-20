from sr_olthad.olthad import TaskNode, TaskStatus

# NOTE: Mock data objects for prompts, hence the setting of "private" attributes directly.

_example_task_in_question = TaskNode(
    _id="1.3.1",
    _parent_id="1.3",
    _task="Do a sub-sub-thing.",
    _status=TaskStatus.IN_PROGRESS,
    _retrospective=None,
)

_example_olthad = TaskNode(
    _id="1",
    _parent_id=None,
    _task="Do a thing.",
    _status=TaskStatus.IN_PROGRESS,
    _retrospective=None,
    _non_planned_subtasks=[
        TaskNode(
            _id="1.1",
            _parent_id="1",
            _task="Do a sub-thing.",
            _status=TaskStatus.SUCCESS,
            _retrospective="This sub-thing was accomplished by doing X, Y, and Z.",
        ),
        TaskNode(
            _id="1.2",
            _parent_id="1",
            _task="Do another sub-thing.",
            _status=TaskStatus.DROPPED,
            _retrospective="This sub-thing wasn't worth pursuing further in light of A, B, and C.",
        ),
        TaskNode(
            _id="1.3",
            _parent_id="1",
            _task="Do this other sub-thing.",
            _status=TaskStatus.IN_PROGRESS,
            _retrospective=None,
            _non_planned_subtasks=[
                _example_task_in_question,
            ],
            _planned_subtasks=[
                TaskNode(
                    _id="1.3.2",
                    _parent_id="1.3",
                    _task="Do another sub-sub-thing.",
                    _status=TaskStatus.PLANNED,
                    _retrospective=None,
                ),
            ],
        ),
    ],
    _planned_subtasks=[
        TaskNode(
            _id="1.4",
            _parent_id="1",
            _task="Do yet another sub-thing.",
            _status=TaskStatus.PLANNED,
            _retrospective=None,
        ),
    ],
)

EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT = _example_task_in_question.stringify()
EXAMPLE_OLTHAD_FOR_SYS_PROMPT = _example_olthad.stringify()
