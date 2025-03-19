import difflib
import inspect
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import ClassVar, Dict, Generator, List, Optional, Tuple

from sr_olthad.config import SrOlthadCfg as cfg
from sr_olthad.schema import DiffLines, GetApprovalBeforeUpdateGenerator

# TODO: How does the "Forgetter" agent update the OLTHAD?
# ...Removing one node at a time?
# ...Removing/summarizing retrospectives?


class AttemptedTaskStatus(StrEnum):
    """Statuses that indicate that a task was attempted."""

    IN_PROGRESS = "In progress"
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

    IN_PROGRESS = AttemptedTaskStatus.IN_PROGRESS
    SUCCESS = AttemptedTaskStatus.SUCCESS
    PARTIAL_SUCCESS = AttemptedTaskStatus.PARTIAL_SUCCESS
    DROPPED = BacktrackedFromTaskStatus.DROPPED
    FAILURE = AttemptedTaskStatus.FAILURE
    PLANNED = "Tentatively planned"


class OlthadCorruptionError(Exception):
    pass


@dataclass
class OlthadTraversal:
    root_node: "TaskNode"
    cur_node: "TaskNode"
    nodes: Dict[str, "TaskNode"]

    def update_status_and_retrospective_of_rood_node(
        self,
        new_status: TaskStatus,
        new_retrospective: str,
        should_yield_diff_and_receive_approval_before_update: bool = False,
    ) -> None | GetApprovalBeforeUpdateGenerator:
        """
        Updates the status and retrospective of the root node.

        NOTE: Should only be called when exiting highest-level task.
        """
        if new_status == TaskStatus.IN_PROGRESS:
            raise OlthadCorruptionError(
                f"{TaskStatus.IN_PROGRESS} was passed as the new status to "
                "`set_root_node_status_and_retrospective`."
            )

        should_do_updates = True
        if should_yield_diff_and_receive_approval_before_update:
            root_node_copy_w_updates = TaskNode(
                id=self.root_node.id,
                parent_id=self.root_node.parent_id,
                task=self.root_node.task,
                status=new_status,
                retrospective=new_retrospective,
                # No need to have these for `.stringify()`
                _non_planned_subtasks=[],
                _planned_subtasks=[],
            )
            # Get the diff and await approval
            should_do_updates = yield self.root_node.stringify(
                pending_node_updates={
                    self.root_node.id: root_node_copy_w_updates
                }
            )

        if should_do_updates:
            self.root_node.retrospective = new_retrospective
            self.root_node.status = new_status
        yield  # Final yield to ensure the generator is closed


@dataclass
class TaskNode:
    """
    A node in an OLTHAD (Open-Language Task Hierarchy of Any Depth).

    NOTE: External contexts CANNOT set attributes of this class. Please rely on public
    methods to update the state of the node/OLTHAD.
    """

    # Class-level stringification constants
    REDACTED_PLANS_STR: ClassVar[str] = "(FUTURE PLANNED TASKS REDACTED)"
    OBFUSCATED_STATUS_STR: ClassVar[str] = "?"
    DONT_STRINGIFY_ATTRS: ClassVar[list[str]] = [
        "parent_id",
        "_non_planned_subtasks",
        "_planned_subtasks",
    ]

    # NOTE: Stringification of these attrs follows order of appearance!
    id: str  # The uid, e.g. 1.3.2
    parent_id: Optional[str]  # The uid or `None` if root node of OLTHAD
    task: str
    status: TaskStatus
    retrospective: Optional[str]
    _non_planned_subtasks: List["TaskNode"] = field(default_factory=list)
    _planned_subtasks: List["TaskNode"] = field(default_factory=list)

    def __setattr__(self, name, value):
        """
        Custom __setattr__ dunder method to prevent external contexts from setting attrs.
        """
        stack = inspect.stack()
        caller_frame = stack[1]
        caller_self = caller_frame.frame.f_locals.get("self", None)
        if isinstance(caller_self, TaskNode) or isinstance(
            caller_self, OlthadTraversal
        ):
            object.__setattr__(self, name, value)
        else:
            raise AttributeError(
                "Cannot set `TaskNode` attrs outside of `TaskNode` or `OlthadTraversal` methods"
            )

    def __str__(self) -> str:
        return self.stringify()

    @property
    def subtasks(self) -> List["TaskNode"]:
        """All subtasks of the node, non-planned and planned."""
        return self._non_planned_subtasks + self._planned_subtasks

    @property
    def in_progress_subtask(self) -> Optional["TaskNode"]:
        """The in-progress subtask of the node, if any.

        Raises:
            OlthadCorruptionError: If there are planned subtasks but no in-progress
                subtasks.
        """

        if not self._non_planned_subtasks:
            if self._planned_subtasks:
                raise OlthadCorruptionError(
                    "If there are planned subtasks, there must be an in-progress subtasks"
                )
            return None
        if (
            self._planned_subtasks
            and self._non_planned_subtasks[-1].status != TaskStatus.IN_PROGRESS
        ):
            # Then we should have already made the 1st planned subtask be the in-progress
            raise OlthadCorruptionError(
                "Subtasks at `self._non_planned_subtasks[-1]` must be in-progress if "
                "there are planned subtasks."
            )
        return self._non_planned_subtasks[-1]

    def remove_subtasks(self) -> None:
        """Removes all of the node's subtasks."""
        self._non_planned_subtasks = []
        self._planned_subtasks = []

    def update_planned_subtasks(
        self,
        new_planned_subtasks: List["TaskNode"],
        should_yield_diff_and_receive_approval_before_update: bool = False,
        diff_root_node: Optional["TaskNode"] = None,
    ) -> None | GetApprovalBeforeUpdateGenerator:
        """
        Replaces the planned subtasks (if any) of the node with the provided list of new
        planned subtasks.

        Args:
            new_planned_subtasks (List[TaskNode]): The new planned subtasks to replace
                the existing planned subtasks with.
            ... # TODO: Finish docstring

        Raises:
            OlthadCorruptionError: If any `new_planned_subtask` has a status other than
                `TaskStatus.PLANNED`.
            OlthadCorruptionError: If any `new_planned_subtask` does not point to the
                parent node.
            OlthadCorruptionError: If any `new_planned_subtask` has subtasks.
            ValueError: If approval requested without a `diff_root_node` being
        """
        if (
            should_yield_diff_and_receive_approval_before_update is True
            and not isinstance(diff_root_node, TaskNode)
        ):
            raise ValueError(
                "If `should_yield_diff_and_receive_approval_before_update` is `True`, "
                "a `diff_root_node` must be provided."
            )
        for subtask in new_planned_subtasks:
            if subtask.status != TaskStatus.PLANNED:
                raise OlthadCorruptionError(
                    "All subtasks must have status `TaskStatus.PLANNED`"
                )
            if subtask.parent_id != self.id:
                raise OlthadCorruptionError(
                    "All subtasks must point to their parent: {self.id}"
                )
            if subtask.subtasks:
                raise OlthadCorruptionError(
                    "Updating planned subtasks with tasks that have subtasks is not "
                    "allowed."
                )

        should_do_updates = True
        if should_yield_diff_and_receive_approval_before_update:
            node_updates = {node.id: node for node in new_planned_subtasks}
            should_do_updates = yield diff_root_node.stringify(
                pending_node_updates=node_updates
            )

        if should_do_updates:
            self._planned_subtasks = new_planned_subtasks
        yield  # Final yield to ensure the generator is closed

    def update_status_and_retrospective_of_in_progress_subtask(
        self,
        new_status: TaskStatus,
        new_retrospective: str,
        should_yield_diff_and_receive_approval_before_update: bool = False,
        diff_root_node: Optional["TaskNode"] = None,
    ) -> None | GetApprovalBeforeUpdateGenerator:
        """
        Updates the status and retrospective of the node.

        Args:
            new_status (TaskStatus): The new status to assign to the node.
            new_retrospective (str): The new retrospective to assign to the node.
            ... # TODO: Finish docstring

        Raises:
            OlthadCorruptionError: If new_status is `TaskStatus.IN_PROGRESS`
            ValueError: If approval requested without a `diff_root_node` being provided
        """
        if new_status == TaskStatus.IN_PROGRESS:
            raise OlthadCorruptionError(
                f"{TaskStatus.IN_PROGRESS} was passed as the new status to "
                "`update_status_and_retrospective_of_in_progress_subtask`."
            )
        if (
            should_yield_diff_and_receive_approval_before_update is True
            and not isinstance(diff_root_node, TaskNode)
        ):
            raise ValueError(
                "If `should_yield_diff_and_receive_approval_before_update` is `True`, "
                "a `diff_root_node` must be provided."
            )

        should_do_updates = True
        if should_yield_diff_and_receive_approval_before_update:
            in_progress_subtask_copy_w_updates = TaskNode(
                id=self.in_progress_subtask.id,
                parent_id=self.in_progress_subtask.parent_id,
                task=self.in_progress_subtask.task,
                status=new_status,
                retrospective=new_retrospective,
                # No need to have these for `.stringify()`
                _non_planned_subtasks=[],
                _planned_subtasks=[],
            )
            # Get the diff and await approval
            should_do_updates = yield diff_root_node.stringify(
                pending_node_updates={
                    self.in_progress_subtask.id: in_progress_subtask_copy_w_updates
                }
            )

        if should_do_updates:
            # Update the status and retrospective of the in-progress subtask
            #   NOTE: Must set retrospective first to avoid accessing `in_progress_subtask`
            #   property with a corrupt state (where in-progress subtask status is not
            #   actually in-progress)
            self.in_progress_subtask.retrospective = new_retrospective
            self.in_progress_subtask.status = new_status
            # Make the next-most planned subtask the new in-progress subtask
            if self._planned_subtasks:
                new_in_progress_subtasks = self._planned_subtasks.pop(0)
                new_in_progress_subtasks.status = TaskStatus.IN_PROGRESS
                self._non_planned_subtasks.append(new_in_progress_subtasks)
            yield  # Final yield to ensure the generator is closed

    def iter_in_progress_descendants(
        self,
    ) -> Generator[Tuple["TaskNode", "TaskNode"], None, None]:
        """
        Generator that gradually rebuilds the node's tree of descendents, yielding
        the PARTIALLY REBUILT root alongside the current depth level's "in-progress"
        node.

        NOTE: This method should only be called if the node is in-progress.

        Yields:
            Tuple[TaskNode, TaskNode]: Tuple where the first element is the partially
                rebuilt root node and the second element is the current depth level's
                "in-progress" node.
        """

        if self.status != TaskStatus.IN_PROGRESS:
            raise ValueError(
                "This method should only ever be called on a node that is in-progress"
            )

        childless_copy_of_self = TaskNode(
            id=self.id,
            parent_id=self.parent_id,
            task=self.task,
            status=self.status,
            retrospective=self.retrospective,
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
                    id=subtask.id,
                    parent_id=subtask.parent_id,
                    task=subtask.task,
                    status=subtask.status,
                    retrospective=subtask.retrospective,
                    # (No further subtasks since this is a level-by-level rebuild)
                    _non_planned_subtasks=[],
                    _planned_subtasks=[],
                )
                if subtask.status == TaskStatus.PLANNED:
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
        pending_node_updates: Optional[Dict[str, "TaskNode"]] = None,
        get_diff_lines: Optional[bool] = None,
    ) -> str | DiffLines:
        """
        Stringifies the task node to get an LM-friendly string.

        NOTE: If `pending_node_updates` is provided, this function will return a
            `DiffLines` object (List[str]).

        Args:
            indent (int): The number of spaces to indent each level of the task node.
            redact_planned_subtasks_below (Optional[str], optional): If provided, all
                planned subtasks below this task will be redacted. Defaults to None.
            obfuscate_status_of (Optional[str], optional): If provided, the status of the
                task with this description will be obfuscated. Defaults to None.
            pending_node_updates (Optional[List[TaskNode]], optional): If provided, this
                function will return a `DiffLines` object (List[str]).

        Returns:
            str | DiffLines: The string representation or the `DiffLines` (List[str]) if
                `pending_node_updates` is provided.
        """
        indent = " " * indent
        output_str = ""
        output_str_w_updates = ""

        def _get_partial_json_dumps(
            node: TaskNode,
            indent_lvl: int,
        ) -> str:
            partial_node_dict = {}
            for key, value in node.__dict__.items():
                if key in TaskNode.DONT_STRINGIFY_ATTRS:
                    continue
                if (
                    obfuscate_status_of is not None
                    and key == "status"
                    and node.id == obfuscate_status_of
                ):
                    value = TaskNode.OBFUSCATED_STATUS_STR
                partial_node_dict[key] = value
            partial_node_str = json.dumps(partial_node_dict, indent=indent)
            lines = partial_node_str[:-2].split("\n")
            partial_node_str_with_cur_indent = ""
            prepend = "\n" + indent * indent_lvl
            for i, line in enumerate(lines):
                indented_line = prepend + line
                partial_node_str_with_cur_indent += indented_line
            return partial_node_str_with_cur_indent

        def increment_node_str_to_output_str(
            node: TaskNode,
            indent_lvl: int = 0,
            should_redact_planned: bool = False,
        ) -> str:
            nonlocal output_str
            nonlocal output_str_w_updates

            if (
                pending_node_updates is not None
                and node.id in pending_node_updates
            ):
                node_for_update = pending_node_updates[node.id]
            else:
                node_for_update = node

            output_str += _get_partial_json_dumps(node, indent_lvl) + ",\n"

            if node_for_update is not None:
                partial_dumps = _get_partial_json_dumps(
                    node_for_update, indent_lvl
                )
                output_str_w_updates += partial_dumps
                output_str_w_updates += ",\n"

            # Check if we should redact this node's planned subtasks
            if (
                redact_planned_subtasks_below is not None
                and node.id == redact_planned_subtasks_below
            ):
                should_redact_planned = True

            if len(node.subtasks) > 0:
                # Open the subtasks list/array
                prepend = indent * (indent_lvl + 1)
                output_str += prepend + '"subtasks": ['
                if node_for_update is not None:
                    output_str_w_updates += prepend + '"subtasks": ['

                # Iterate through subtasks
                n_subtasks = len(node.subtasks)
                for i, subtask in enumerate(node.subtasks):

                    # Check if we've reached a planned subtask that should be redacted
                    if (
                        should_redact_planned
                        and subtask.status == TaskStatus.PLANNED
                    ):
                        # Redact from here on (break the loop)
                        prepend = "\n" + indent * (indent_lvl + 2)
                        output_str += prepend + TaskNode.REDACTED_PLANS_STR
                        if node_for_update is not None:
                            output_str_w_updates += prepend
                            output_str_w_updates += TaskNode.REDACTED_PLANS_STR
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
                            output_str_w_updates += ","

                # Finally, close the subtasks list/array
                prepend = "\n" + indent * (indent_lvl + 1)
                output_str += prepend + "]\n"
                if node_for_update is not None:
                    output_str_w_updates += prepend + "]\n"
            else:
                prepend = indent * (indent_lvl + 1)
                output_str += prepend + '"subtasks": null\n'
                if node_for_update is not None:
                    output_str_w_updates += prepend + '"subtasks": null\n'

            # Close the node dict/object string after incrementing subtasks
            prepend = indent * indent_lvl
            output_str += prepend + "}"
            if node_for_update is not None:
                output_str_w_updates += prepend + "}"

        increment_node_str_to_output_str(self)
        if pending_node_updates:
            # Create/return `DiffLines` object (List[str]) and return it
            differ = difflib.Differ()
            diff_lines = differ.compare(
                # TODO: Possible optimization - changing above logic to have
                # appended lines to a list in order to avoid this split
                output_str.splitlines(keepends=True),
                output_str_w_updates.splitlines(keepends=True),
            )
            return list(diff_lines)
        elif get_diff_lines:
            # Sometimes we want to get a diff even when there's no pending updates
            output_lines = output_str.splitlines(keepends=True)
            return list(difflib.Differ().compare(output_lines, output_lines))
        else:
            return output_str
