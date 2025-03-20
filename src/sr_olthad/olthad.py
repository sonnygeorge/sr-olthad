import difflib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Callable, ClassVar, Dict, Generator, List, Optional, Tuple

from sr_olthad.config import SrOlthadCfg as cfg

# TODO: How would the "Forgetter" agent update the OLTHAD?
# ...Pruning one node at a time?
# ...Removing/summarizing retrospectives?


class AttemptedTaskStatus(StrEnum):
    """Statuses that indicate that a task was attempted."""

    SUCCESS = "Attempted (success)"
    PARTIAL_SUCCESS = "Attempted (partial success)"
    FAILURE = "Attempted (failure)"


class BacktrackedFromTaskStatus(StrEnum):
    """Statuses that warrant backtracking or indicate that backtracking occured."""

    SUCCESS = AttemptedTaskStatus.SUCCESS
    PARTIAL_SUCCESS = AttemptedTaskStatus.PARTIAL_SUCCESS
    FAILURE = AttemptedTaskStatus.FAILURE
    DROPPED = "Dropped"


class TaskStatus(StrEnum):
    """All possible statuses for a task"""

    IN_PROGRESS = "In progress"
    SUCCESS = AttemptedTaskStatus.SUCCESS
    PARTIAL_SUCCESS = AttemptedTaskStatus.PARTIAL_SUCCESS
    DROPPED = BacktrackedFromTaskStatus.DROPPED
    FAILURE = AttemptedTaskStatus.FAILURE
    PLANNED = "Tentatively planned"


@dataclass
class PendingOlthadUpdate:
    _do_update: Callable[[], None]
    _get_diff: Callable[[], List[str]]

    def get_diff(self) -> List[str]:
        return self._get_diff()

    def commit(self) -> None:
        self._do_update()


class OlthadUsageError(Exception):
    pass


class CorruptedOlthadError(Exception):
    pass


@dataclass
class OlthadTraversal:
    """
    An (ongoing) traversal of an OLTHAD (Open-Language Task Hierarchy of Any Depth).

    NOTE: By design, this class "sees" (and does whatever with) the "private" attributes
    (the ones whose names being with an underscore) of the `TaskNode` class.
    """

    _root_node: "TaskNode"
    _cur_node: "TaskNode"
    _nodes: Dict[str, "TaskNode"]

    def __init__(self, highest_level_task: str):
        self._root_node = TaskNode(
            _id="1",
            _parent_id=None,
            _task=highest_level_task,
            _status=TaskStatus.IN_PROGRESS,
            _retrospective=None,
        )
        self._cur_node = self._root_node
        self._nodes = {self._root_node.id: self._root_node}

    @property
    def cur_node(self) -> "TaskNode":
        return self._cur_node

    @property
    def root_node(self) -> "TaskNode":
        return self._root_node

    @property
    def nodes(self) -> Dict[str, "TaskNode"]:
        return self._nodes

    def backtrack_to(self, node_id: str | None) -> None:
        if node_id is None:  # Skip below if backtracking out of the root node
            self._cur_node = None
            return

        if node_id not in self._nodes:
            msg = f"Node with id '{node_id}' not found in `self.nodes`"
            raise OlthadUsageError(msg)

        # Prune children and backtrack until the cur_node is the child of the target node
        # This prevents grandchildren after backtracking
        while self._cur_node._parent_id != node_id:
            if self._cur_node.is_root():
                msg = "Provided `node_id` is not an ancestor of the current node."
                raise OlthadUsageError(msg)

            # Prune subtasks
            for subtask_node in self._cur_node.subtasks:
                del self._nodes[subtask_node._id]
            self._cur_node._non_planned_subtasks = []
            self._cur_node._planned_subtasks = []

            # Backtrack
            self._cur_node = self._nodes[self._cur_node._parent_id]

        # Backtrack once more since we know the node_id == self.cur_node.parent_id
        self._cur_node = self._nodes[self._cur_node._parent_id]

    def recurse_inward(self) -> None:
        """Sets the current node to the in-progress subtask."""
        self._cur_node = self._cur_node.in_progress_subtask

    def update_planned_subtasks_of_cur_node(
        self, new_planned_subtasks: List[str]
    ) -> PendingOlthadUpdate:

        if len(new_planned_subtasks) == 0:
            msg = "The list of new planned subtasks cannot be empty."
            raise OlthadUsageError(msg)

        new_subtask_node_objects: List["TaskNode"] = []
        for i, new_planned_subtask in enumerate(new_planned_subtasks):
            new_subtask_node = TaskNode(
                _id=f"{self._cur_node._id}.{i+1}",
                _parent_id=self._cur_node._id,
                _task=new_planned_subtask,
                _status=TaskStatus.PLANNED,
                _retrospective=None,
            )
            new_subtask_node_objects.append(new_subtask_node)

        def do_update():
            for new_subtask_node in new_subtask_node_objects:
                self._nodes[new_subtask_node._id] = new_subtask_node
            self._cur_node._planned_subtasks = new_subtask_node_objects
            if (
                len(self._cur_node._non_planned_subtasks) > 0
                and self._cur_node._non_planned_subtasks[-1]._status
                != TaskStatus.IN_PROGRESS
            ):
                # We need to pop the next planned sibling and make it the new in-progress subtask
                next_planned_sibling = self._cur_node._planned_subtasks.pop(0)
                next_planned_sibling._status = TaskStatus.IN_PROGRESS
                self._cur_node._non_planned_subtasks.append(next_planned_sibling)

        def get_diff():
            pending_changes = {n._id: n for n in new_subtask_node_objects}
            return self._root_node.stringify(pending_changes=pending_changes)

        return PendingOlthadUpdate(
            _do_update=do_update,
            _get_diff=get_diff,
        )

    def update_status_and_retrospective_of(
        self,
        node: "TaskNode",
        new_status: BacktrackedFromTaskStatus | AttemptedTaskStatus,
        new_retrospective: str,
    ):
        if node != self._cur_node and self.cur_node not in self._cur_node.subtasks:
            msg = "`node` can only be the current node or one of its subtasks."
            raise OlthadUsageError(msg)

        if node.status != TaskStatus.IN_PROGRESS:
            msg = "This method should only be called on an in-progress task."
            raise OlthadUsageError(msg)

        if new_status == TaskStatus.IN_PROGRESS:
            raise OlthadUsageError(
                f"{TaskStatus.IN_PROGRESS} was passed as the new status to "
                "`update_status_and_retrospective_od`, which is not allowed/supported."
            )

        def do_update():
            node._retrospective = new_retrospective
            node._status = new_status

            if node._parent_id is None:
                return

            # Because we know we've just changed the status of an in-progress (sub)task,
            # we need to make the next planned sibling (if one exists) be the new
            # in-progress (sub)task for their mutual parent.
            parent = self._nodes[node._parent_id]
            if len(parent._planned_subtasks) > 0:
                next_planned_sibling = parent._planned_subtasks.pop(0)
                next_planned_sibling._status = TaskStatus.IN_PROGRESS
                parent._non_planned_subtasks.append(next_planned_sibling)

        def get_diff():
            pending_change = TaskNode(
                _id=node._id,
                _parent_id=node._parent_id,
                _task=node._task,
                _status=new_status,  # (changed)
                _retrospective=new_retrospective,  # (changed)
            )
            pending_changes = {node.id: pending_change}

            # (See above comment for why this is also a pending change)
            parent = None
            if node._parent_id is not None:
                parent = self._nodes[node._parent_id]
            if parent is not None and len(parent._planned_subtasks) > 0:
                next_planned_sibling = parent._planned_subtasks[0]
                pending_change = TaskNode(
                    _id=next_planned_sibling._id,
                    _parent_id=next_planned_sibling._parent_id,
                    _task=next_planned_sibling._task,
                    _status=TaskStatus.IN_PROGRESS,  # (changed)
                    _retrospective=next_planned_sibling._retrospective,
                )
                pending_changes[next_planned_sibling._id] = pending_change

            return self._root_node.stringify(pending_changes=pending_changes)

        return PendingOlthadUpdate(
            _do_update=do_update,
            _get_diff=get_diff,
        )


@dataclass
class TaskNode:
    """A node in an OLTHAD (Open-Language Task Hierarchy of Any Depth)."""

    _REDACTED_PLANS_STR: ClassVar[str] = "(FUTURE PLANNED TASKS REDACTED)"
    _OBFUSCATED_STATUS_STR: ClassVar[str] = "?"

    _id: str
    _task: str
    _status: TaskStatus
    _retrospective: Optional[str]
    _parent_id: Optional[str]
    _non_planned_subtasks: List["TaskNode"] = field(default_factory=list)
    _planned_subtasks: List["TaskNode"] = field(default_factory=list)

    def __str__(self) -> str:
        return self.stringify()

    @property
    def id(self) -> str:
        return self._id

    @property
    def task(self) -> str:
        return self._task

    @property
    def status(self) -> TaskStatus:
        return self._status

    @property
    def retrospective(self) -> str | None:
        return self._retrospective

    @property
    def parent_id(self) -> str | None:
        return self._parent_id

    @property
    def subtasks(self) -> List["TaskNode"]:
        return self._non_planned_subtasks + self._planned_subtasks

    @property
    def in_progress_subtask(self) -> Optional["TaskNode"]:
        return self._get_in_progress_subtask()

    def _get_in_progress_subtask(self) -> Optional["TaskNode"]:
        if len(self._non_planned_subtasks) == 0 and len(self._planned_subtasks) == 0:
            return None

        if len(self._non_planned_subtasks) == 0 or (
            self._non_planned_subtasks[-1]._status != TaskStatus.IN_PROGRESS
        ):
            raise CorruptedOlthadError(
                "`self._non_planned_subtasks[-1]` must be in-progress if there are "
                "planned subtasks."
            )

        return self._non_planned_subtasks[-1]

    def is_root(self) -> bool:
        """Returns whether the node is the root of an OLTHAD."""
        return self._parent_id is None

    def iter_in_progress_descendants(
        self,
    ) -> Generator[Tuple["TaskNode", "TaskNode"], None, None]:
        """
        Generator that gradually rebuilds the node's tree of descendents, yielding
        the PARTIALLY REBUILT root alongside the current depth level's "in-progress"
        node.

        NOTE: This method should only be called if the node is in-progress.

        Yields:
            Tuple[TaskNode, TaskNode]: Tuple where the first item is the partially
                rebuilt root node and the second item is the current depth level's
                "in-progress" node.
        """

        if self._status != TaskStatus.IN_PROGRESS:
            raise ValueError(
                "This method should only ever be called if the node is in-progress"
            )

        childless_copy_of_self = TaskNode(
            _id=self._id,
            _parent_id=self._parent_id,
            _task=self._task,
            _status=self._status,
            _retrospective=self._retrospective,
            # (No further subtasks since this is a level-by-level rebuild)
            _non_planned_subtasks=[],
            _planned_subtasks=[],
        )

        cur_in_progress_node_childless_copy = childless_copy_of_self
        cur_in_progress_node = self

        # Name change for readability since during rebuild it will get children
        root_of_rebuild = childless_copy_of_self

        while True:
            yield root_of_rebuild, cur_in_progress_node_childless_copy

            if len(cur_in_progress_node.subtasks) == 0:  # If rebuild complete
                break

            for i, subtask in enumerate(cur_in_progress_node.subtasks):
                # Rebuild subtask and add it to the rebuild
                subtask_childless_copy = TaskNode(
                    _id=subtask._id,
                    _parent_id=subtask._parent_id,
                    _task=subtask._task,
                    _status=subtask._status,
                    _retrospective=subtask._retrospective,
                    # (No further subtasks since this is a level-by-level rebuild)
                    _non_planned_subtasks=[],
                    _planned_subtasks=[],
                )
                if subtask._status == TaskStatus.PLANNED:
                    cur_in_progress_node_childless_copy._planned_subtasks.append(
                        subtask_childless_copy
                    )
                else:
                    cur_in_progress_node_childless_copy._non_planned_subtasks.append(
                        subtask_childless_copy
                    )

                cur_in_progress_node = cur_in_progress_node.in_progress_subtask
                cur_in_progress_node_childless_copy = (
                    cur_in_progress_node_childless_copy.in_progress_subtask
                )

    def stringify(
        self,
        indent: int = cfg.JSON_DUMPS_INDENT,
        redact_planned_subtasks_below: Optional[str] = None,
        obfuscate_status_of: Optional[str] = None,
        pending_changes: Optional[Dict[str, "TaskNode"]] = None,
        get_diff_lines: bool = False,
    ) -> str | List[str]:
        """
        Stringifies the task node to get an LM-friendly string.

        NOTE: If `pending_node_updates` is provided, this function will return a
            "diff" (List[str]).

        Args:
            indent (int): The number of spaces to indent each level of the task node.
            redact_planned_subtasks_below (Optional[str], optional): If provided, all
                planned subtasks below this task will be redacted. Defaults to None.
            obfuscate_status_of (Optional[str], optional): If provided, the status of the
                task with this description will be obfuscated. Defaults to None.
            pending_changes (Optional[List[TaskNode]], optional): If provided, this
                function will return a "diff" (List[str]).
            get_diff_lines (Optional[bool], optional): If True, this function will return
                a "diff" (List[str]). Defaults to False.

        Returns:
            str | List[str]: The string representation or the "diff" (List[str]) if
                `pending_changes` is provided or `get_diff_lines` is True.
        """

        def get_partial_json_dumps(
            node: TaskNode,
            indent_lvl: int,
        ) -> str:
            if node._id != obfuscate_status_of:
                status_str = node._status
            else:
                status_str = TaskNode._OBFUSCATED_STATUS_STR
            partial_node_dict = {
                "id": node._id,
                "task": node._task,
                "status": status_str,
                "retrospective": node._retrospective,
            }
            dumps = json.dumps(partial_node_dict, indent=indent)
            lines = dumps[:-2].split("\n")
            with_cur_indent = ""
            prepend = "\n" + indent * indent_lvl
            for i, line in enumerate(lines):
                indented_line = prepend + line
                with_cur_indent += indented_line
            return with_cur_indent

        indent = " " * indent
        output_str = ""
        output_str_w_changes = ""

        def increment_node_str_to_output_str(
            node: TaskNode,
            indent_lvl: int = 0,
            should_redact_planned: bool = False,
        ) -> str:
            nonlocal output_str
            nonlocal output_str_w_changes

            if pending_changes is not None and node._id in pending_changes:
                node_for_update = pending_changes[node._id]
            else:
                node_for_update = node

            output_str += get_partial_json_dumps(node, indent_lvl) + ",\n"

            if node_for_update is not None:
                partial_dumps = get_partial_json_dumps(node_for_update, indent_lvl)
                output_str_w_changes += partial_dumps
                output_str_w_changes += ",\n"

            # Check if we should redact this node's planned subtasks
            if (
                redact_planned_subtasks_below is not None
                and node._id == redact_planned_subtasks_below
            ):
                should_redact_planned = True

            if len(node.subtasks) > 0:
                # Open the subtasks list/array
                prepend = indent * (indent_lvl + 1)
                output_str += prepend + '"subtasks": ['
                if node_for_update is not None:
                    output_str_w_changes += prepend + '"subtasks": ['

                # Iterate through subtasks
                n_subtasks = len(node.subtasks)
                for i, subtask in enumerate(node.subtasks):

                    # Check if we've reached a planned subtask that should be redacted
                    if should_redact_planned and subtask._status == TaskStatus.PLANNED:
                        # Redact from here on (break the loop)
                        prepend = "\n" + indent * (indent_lvl + 2)
                        output_str += prepend + TaskNode._REDACTED_PLANS_STR
                        if node_for_update is not None:
                            output_str_w_changes += prepend
                            output_str_w_changes += TaskNode._REDACTED_PLANS_STR
                        break

                    # Recursive call to increment the subtask to the output string
                    increment_node_str_to_output_str(
                        node=subtask,
                        indent_lvl=indent_lvl + 2,
                        should_redact_planned=should_redact_planned,
                    )

                    # Add comma if not last subtask
                    if i < n_subtasks - 1:
                        output_str += ","
                        if node_for_update is not None:
                            output_str_w_changes += ","

                # Finally, close the subtasks list/array
                prepend = "\n" + indent * (indent_lvl + 1)
                output_str += prepend + "]\n"
                if node_for_update is not None:
                    output_str_w_changes += prepend + "]\n"
            else:
                prepend = indent * (indent_lvl + 1)
                output_str += prepend + '"subtasks": null\n'
                if node_for_update is not None:
                    output_str_w_changes += prepend + '"subtasks": null\n'

            # Close the node dict/object string after incrementing subtasks
            prepend = indent * indent_lvl
            output_str += prepend + "}"
            if node_for_update is not None:
                output_str_w_changes += prepend + "}"

        increment_node_str_to_output_str(self)
        output_str = output_str.strip()
        output_str_w_changes = output_str_w_changes.strip()
        if pending_changes:
            # Create/return "diff" (List[str]) and return it
            differ = difflib.Differ()
            diff = differ.compare(
                # TODO: Possible optimization - changing above logic to have
                # appended lines to a list in order to avoid this split
                output_str.splitlines(keepends=True),
                output_str_w_changes.splitlines(keepends=True),
            )
            return list(diff)
        elif get_diff_lines:
            # Sometimes we want to get a "diff" even when there's no pending changes
            output_lines = output_str.splitlines(keepends=True)
            return list(difflib.Differ().compare(output_lines, output_lines))
        else:
            return output_str
