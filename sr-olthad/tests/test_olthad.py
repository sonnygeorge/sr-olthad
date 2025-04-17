import re

from sr_olthad.olthad import TaskNode
from sr_olthad.schema import TaskStatus


class TestTaskNode:
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

    def test_stringify_w_obfuscate_status_of(self):
        """
        Confirms that the string used to obfuscate statuses is in the expected location
        of the stringify results (and not the status).
        """
        root = TestTaskNode.DUMMY_ROOT_TASK_NODE
        in_question = TestTaskNode.DUMMY_TASK_IN_QUESTION
        stringified = root.stringify(obfuscate_status_of=in_question.id)
        obfuscated_str = root._OBFUSCATED_STATUS_STR

        # Verify presence of obfuscated_str
        assert obfuscated_str in stringified

        # Verify the presence of and find the string that should precede the obfuscated_str
        before_obfuscated_str_pattern = r'"id": "1\.1",\s*"task": ".+",\s*"status": "'
        before_obfuscated_str_match = re.search(before_obfuscated_str_pattern, stringified)
        assert before_obfuscated_str_match is not None
        assert isinstance(before_obfuscated_str_match, re.Match)
        idx_just_before_obfuscated_str = before_obfuscated_str_match.end()

        # Verify that the obfuscated_str is in the expected location
        should_start_with_obfuscated_str = stringified[idx_just_before_obfuscated_str:]
        assert should_start_with_obfuscated_str.startswith(obfuscated_str), (
            f"Expected result to start with {obfuscated_str}, got: {should_start_with_obfuscated_str[:50]}"
        )

        # Verify that the status (that should be obfuscated) is not there somehow as well
        idx_of_subtasks = should_start_with_obfuscated_str.index("subtasks")
        should_not_contain_status = should_start_with_obfuscated_str[:idx_of_subtasks]
        assert in_question.status not in should_not_contain_status

    def test_stringify_w_redact_planned_subtasks_below(self):
        root = TestTaskNode.DUMMY_ROOT_TASK_NODE
        in_question = TestTaskNode.DUMMY_TASK_IN_QUESTION
        stringified = root.stringify(redact_planned_subtasks_below=in_question.id)
        in_question_planned_subtasks_are_present = "1.1.4" in stringified
        assert not in_question_planned_subtasks_are_present
        assert root._REDACTED_PLANS_STR in stringified


if __name__ == "__main__":
    test = TestTaskNode()
    test.test_stringify_w_obfuscate_status_of()
    test.test_stringify_w_redact_planned_subtasks_below()
    # Print to sanity check
    print(
        test.DUMMY_ROOT_TASK_NODE.stringify(
            obfuscate_status_of=test.DUMMY_TASK_IN_QUESTION.id,
            redact_planned_subtasks_below=test.DUMMY_TASK_IN_QUESTION.id,
        )
    )
