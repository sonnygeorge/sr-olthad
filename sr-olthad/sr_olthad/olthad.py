"""
Objects/logic relating to OLTHADs: task nodes, pending updates, etc.

NOTE: This module generally shouldn't import from files like sr_olthad.utils, etc. since it
is very high-up in the import hierarchy due to it being imported by sr_olthad.prompts._common
to construct and stringify example OLTHADs for the prompts (which are declared at import time).
"""

import difflib
import json
from collections.abc import Callable, Generator
from dataclasses import dataclass, field
from typing import ClassVar, Self

from sr_olthad.config import SrOlthadCfg
from sr_olthad.schema import TaskStatus

# TODO: How would the "Forgetter" agent update the OLTHAD?
# ...Pruning one node at a time?
# ...Removing/summarizing retrospectives?


@dataclass
class PendingOlthadUpdate:
    _do_update: Callable[[], None]
    _get_diff: Callable[[], list[str]]

    def get_diff(self) -> list[str]:
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
    _nodes: dict[str, "TaskNode"]

    def __init__(self, highest_level_task: str):
        super().__init__()

        self._root_node = TaskNode(
            _id="1",
            _parent_id=None,
            _task=highest_level_task,
            _status=TaskStatus.IN_PROGRESS,
            _retrospective=None,
        )
        self._cur_node: TaskNode | None = self._root_node
        self._nodes = {self._root_node.id: self._root_node}

    @property
    def cur_node(self) -> "TaskNode":
        return self._cur_node

    @property
    def root_node(self) -> "TaskNode":
        return self._root_node

    @property
    def nodes(self) -> dict[str, "TaskNode"]:
        return self._nodes

    def backtrack_to(self, node_id: str | None) -> None:
        if node_id is None:  # Skip below if backtracking out of the root node
            self._cur_node = None
            return

        if node_id not in self._nodes:
            msg = f"Node with id '{node_id}' not found in `self.nodes`"
            raise OlthadUsageError(msg)

        def backtrack_once():
            # Prune subtasks
            for subtask_node in self._cur_node.subtasks:
                del self._nodes[subtask_node._id]
            self._cur_node._non_planned_subtasks = []
            self._cur_node._planned_subtasks = []
            # Backtrack
            self._cur_node = self._nodes[self._cur_node._parent_id]

        # Prune children and backtrack until the cur_node is the child of the target node
        # This prevents grandchildren after backtracking
        while self._cur_node._parent_id != node_id:
            if self._cur_node.is_root():
                msg = "Provided `node_id` is not an ancestor of the current node."
                raise OlthadUsageError(msg)

            backtrack_once()

        # Backtrack once more since we know the node_id == self.cur_node.parent_id
        backtrack_once()

    def recurse_inward(self) -> None:
        assert len(self._cur_node._planned_subtasks) > 0
        new_cur_node = self._cur_node._planned_subtasks.pop(0)
        self._cur_node._non_planned_subtasks.append(new_cur_node)
        self._cur_node = new_cur_node
        self._cur_node._status = TaskStatus.IN_PROGRESS

    def update_planned_subtasks_of_cur_node(
        self, new_planned_subtasks: list[str]
    ) -> PendingOlthadUpdate:
        if len(new_planned_subtasks) == 0:
            msg = "The list of new planned subtasks cannot be empty."
            raise OlthadUsageError(msg)

        new_subtask_node_objects: list[TaskNode] = []
        for i in range(len(new_planned_subtasks)):
            new_planned_subtask = new_planned_subtasks[i]
            id_offset = len(self._cur_node._non_planned_subtasks)
            new_subtask_node = TaskNode(
                _id=f"{self._cur_node._id}.{id_offset + i + 1}",
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

        def get_diff():
            current_node_copy_with_changes = TaskNode(
                _id=self._cur_node._id,
                _parent_id=self._cur_node._parent_id,
                _task=self._cur_node._task,
                _status=self._cur_node._status,
                _retrospective=self._cur_node._retrospective,
                _non_planned_subtasks=self._cur_node._non_planned_subtasks,
                _planned_subtasks=new_subtask_node_objects,
            )
            pending_changes = {self._cur_node.id: current_node_copy_with_changes}
            return self._root_node.stringify(pending_changes=pending_changes)

        return PendingOlthadUpdate(
            _do_update=do_update,
            _get_diff=get_diff,
        )

    def update_status_and_retrospective_of(
        self,
        node: "TaskNode",
        new_status: TaskStatus,
        new_retrospective: str | None = None,
    ):
        is_current_node = node == self._cur_node
        is_subtask = node._parent_id == self._cur_node._id
        is_ancestor = self._cur_node._id.startswith(node._id)
        if not is_current_node and not is_subtask and not is_ancestor:
            msg = "The node to update must be the current node, a subtask of the current node, or an ancestor of the current node."
            raise OlthadUsageError(msg)

        if new_status == TaskStatus.IN_PROGRESS:
            parent = self._nodes[node._parent_id]
            if len(parent._non_planned_subtasks) > 0:
                assert parent._non_planned_subtasks[-1].status != TaskStatus.IN_PROGRESS
                assert parent._planned_subtasks[0].id == node.id

        def do_update():
            node._retrospective = new_retrospective
            node._status = new_status
            if new_status == TaskStatus.IN_PROGRESS:
                # We need to move it into the non-planned subtasks
                # (we've already asserted that it's the first planned subtask)
                self._cur_node._planned_subtasks.remove(node)
                self._cur_node._non_planned_subtasks.append(node)

        def get_diff():
            pending_change = TaskNode(
                _id=node._id,
                _parent_id=node._parent_id,
                _task=node._task,
                _status=new_status,  # (changed)
                _retrospective=new_retrospective,  # (changed)
                _non_planned_subtasks=node._non_planned_subtasks,
                _planned_subtasks=node._planned_subtasks,
            )
            pending_changes = {node.id: pending_change}
            return self._root_node.stringify(pending_changes=pending_changes)

        return PendingOlthadUpdate(
            _do_update=do_update,
            _get_diff=get_diff,
        )

    def update_nothing(self):
        return PendingOlthadUpdate(
            _do_update=lambda: None,
            _get_diff=lambda: self._root_node.stringify(get_diff=True),
        )


@dataclass
class TaskNode:
    """A node in an OLTHAD (Open-Language Task Hierarchy of Any Depth)."""

    _REDACTED_PLANS_STR: ClassVar[str] = "(FUTURE PLANNED TASKS REDACTED)"
    _OBFUSCATED_STATUS_STR: ClassVar[str] = "?"

    _id: str
    _task: str
    _status: TaskStatus
    _retrospective: str | None
    _parent_id: str | None
    _non_planned_subtasks: list[Self] = field(default_factory=list)
    _planned_subtasks: list[Self] = field(default_factory=list)

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
    def subtasks(self) -> list[Self] | None:
        return self._non_planned_subtasks + self._planned_subtasks

    @property
    def in_progress_subtask(self) -> Self | None:
        if len(self._non_planned_subtasks) == 0 and len(self._planned_subtasks) == 0:
            return None
        assert self._non_planned_subtasks[-1].status == TaskStatus.IN_PROGRESS
        return self._non_planned_subtasks[-1]

    @property
    def next_planned_subtask(self) -> Self | None:
        assert len(self._planned_subtasks) > 0
        assert self._planned_subtasks[0]._status == TaskStatus.PLANNED
        return self._planned_subtasks[0]

    def is_root(self) -> bool:
        """Returns whether the node is the root of an OLTHAD."""
        return self._parent_id is None

    def iter_in_progress_descendants(
        self,
    ) -> Generator[tuple[Self, Self, Self], None, None]:
        """
        Generator that gradually rebuilds the node's tree of descendents, yielding
        the PARTIALLY REBUILT root alongside the current depth level's "in-progress"
        node.

        NOTE: This method should only be called if the node is in-progress.

        Yields:
            tuple[TaskNode, TaskNode, TaskNode]: Tuple where:
                - The first element is the root of the rebuild (a copy of the node
                    with no subtasks).
                - The second element is the current depth level's "in-progress" node
                    (a copy of the node with no subtasks).
                - The third element is the current depth level's "in-progress" node
                    (the original node).
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
            yield root_of_rebuild, cur_in_progress_node_childless_copy, cur_in_progress_node

            if len(cur_in_progress_node.subtasks) == 0:  # If rebuild complete
                break

            for subtask in cur_in_progress_node.subtasks:
                # Partially reconstruct subtask
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
                # Add it to the rebuild
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
        indent: int = SrOlthadCfg.JSON_DUMPS_INDENT,
        redact_planned_subtasks_below: str | None = None,
        obfuscate_status_of: str | None = None,
        pending_changes: dict[str, Self] | None = None,
        get_diff: bool = False,
    ) -> str | list[str]:
        """
        Stringifies the task node to get an LM-friendly string.

        NOTE: If `pending_node_updates` is provided, this function will return a
            "diff" (list[str]).

        Args:
            indent (int): The number of spaces to indent each level of the task node.
            redact_planned_subtasks_below (str | None): If provided, all
                planned subtasks below this task will be redacted. Defaults to None.
            obfuscate_status_of (str | None): If provided, the status of the
                task with this description will be obfuscated. Defaults to None.
            pending_changes (list[TaskNode] | None): If provided, this
                function will return a "diff" (list[str]).
            get_diff (bool | None): If True, this function will return
                a "diff" (list[str]). Defaults to False.

        Returns:
            str | list[str]: The string representation or the "diff" (list[str]) if
                `pending_changes` is provided or `get_diff` is True.
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
            for line in lines:
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
            parent_subtasks: list[TaskNode] | None = None,
        ) -> str:
            nonlocal output_str
            nonlocal output_str_w_changes

            parent_is_a_pending_change = (
                node.parent_id is not None
                and pending_changes is not None
                and node.parent_id in pending_changes
            )

            if pending_changes is not None and node._id in pending_changes:
                node_for_update = pending_changes[node._id]
            elif parent_is_a_pending_change and len(parent_subtasks) > 0:
                idx_of_node_in_parent_subtasks = parent_subtasks.index(node)
                if (
                    len(pending_changes[node.parent_id].subtasks)
                    <= idx_of_node_in_parent_subtasks
                ):
                    pass  # Abitrary line of code in order to catch w/ break point

                assert (
                    len(pending_changes[node.parent_id].subtasks)
                    > idx_of_node_in_parent_subtasks
                ), (
                    f"Pending changes for parent node: {len(pending_changes[node.parent_id].subtasks)} | {idx_of_node_in_parent_subtasks}"
                )

                node_for_update = pending_changes[node.parent_id].subtasks[
                    idx_of_node_in_parent_subtasks
                ]
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

            # Increment subtasks
            if parent_is_a_pending_change and node.task != node_for_update.task:
                assert len(node.subtasks) == 0
                assert len(node_for_update.subtasks) == 0
                prepend = indent * (indent_lvl + 1)
                output_str += prepend + '"subtasks": null\n'
                output_str_w_changes += prepend + '"subtasks": null\n'
            elif len(node.subtasks) > 0:
                # Open the subtasks list/array
                prepend = indent * (indent_lvl + 1)
                output_str += prepend + '"subtasks": ['
                if node_for_update is not None:
                    output_str_w_changes += prepend + '"subtasks": ['

                # Iterate through subtasks
                n_subtasks = len(node.subtasks)
                if isinstance(node_for_update, TaskNode):
                    n_subtasks_of_node_for_update = len(node_for_update.subtasks)
                else:
                    n_subtasks_of_node_for_update = 0
                for i in range(max(n_subtasks, n_subtasks_of_node_for_update)):
                    if len(node.subtasks) > i:
                        subtask = node.subtasks[i]
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
                            parent_subtasks=node.subtasks,
                        )
                        # Add comma if not last
                        if i < n_subtasks - 1:
                            output_str += ","
                            if node_for_update is not None:
                                output_str_w_changes += ","
                    else:
                        new_subtask_in_update = node_for_update.subtasks[i]
                        partial_dumps = get_partial_json_dumps(
                            new_subtask_in_update, indent_lvl + 2
                        )
                        output_str_w_changes += partial_dumps + ",\n"
                        prepend = indent * (indent_lvl + 3)
                        output_str_w_changes += prepend + '"subtasks": null\n'
                        prepend = indent * (indent_lvl + 2)
                        output_str_w_changes += prepend + "}"
                        # Add comma if not last
                        if i < n_subtasks_of_node_for_update - 1:
                            output_str_w_changes += ","

                # Finally, close the subtasks list/array
                prepend = "\n" + indent * (indent_lvl + 1)
                output_str += prepend + "]\n"
                if node_for_update is not None:
                    output_str_w_changes += prepend + "]\n"
            elif (
                node_for_update is not None and len(node_for_update.subtasks) > 0
            ):  # I.e., the update = addition of these subtasks
                # Open the subtasks list/array
                prepend = indent * (indent_lvl + 1)
                output_str += prepend + '"subtasks": null\n'
                output_str_w_changes += prepend + '"subtasks": ['
                # Iterate through subtasks
                n_subtasks = len(node_for_update.subtasks)
                for i, subtask in enumerate(node_for_update.subtasks):
                    # Add subtask to the output string with changes
                    subtask_dict = {
                        "id": subtask._id,
                        "task": subtask._task,
                        "status": subtask._status,
                        "retrospective": subtask._retrospective,
                        "subtasks": None,
                    }
                    subtask_dump = json.dumps(
                        subtask_dict, indent=SrOlthadCfg.JSON_DUMPS_INDENT
                    )
                    subtask_dump = "\n".join(  # Add indent to each line
                        [
                            indent * (indent_lvl + 2) + line
                            for line in subtask_dump.splitlines()
                        ]
                    )
                    output_str_w_changes += "\n" + subtask_dump
                    # Add comma if not last subtask
                    if i < n_subtasks - 1:
                        output_str_w_changes += ","
                # Finally, close the subtasks list/array
                prepend = "\n" + indent * (indent_lvl + 1)
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
            # Create/return "diff" (list[str]) and return it
            differ = difflib.Differ()
            diff = differ.compare(
                # TODO: Possible optimization - changing above logic to have
                # appended lines to a list in order to avoid this split
                output_str.splitlines(keepends=True),
                output_str_w_changes.splitlines(keepends=True),
            )
            return list(diff)
        elif get_diff:
            # Sometimes we want to get a "diff" even when there's no pending changes
            output_lines = output_str.splitlines(keepends=True)
            return list(difflib.Differ().compare(output_lines, output_lines))
        else:
            return output_str
