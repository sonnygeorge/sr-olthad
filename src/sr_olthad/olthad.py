import inspect
import json
from dataclasses import dataclass, field
from enum import StrEnum
from typing import ClassVar, Generator, List, Optional, Tuple

from sr_olthad.config import SrOlthadCfg as cfg

# TODO: How does the "Forgetter" agent update the OLTHAD?


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
        "idx_of_next_planned_subtask",
    ]

    # `TaskNode` attributes
    # NOTE: Stringification of these attrs follows order of appearance!
    id: str  # The uid, e.g. 1.3.2
    parent_id: Optional[str]  # The uid or `None` if root node of OLTHAD
    task: str
    status: TaskStatus
    retrospective: Optional[str]
    subtasks: List["TaskNode"] = field(default_factory=list)
    idx_of_next_planned_subtask: Optional[int] = (
        None  # NOTE: Not visible to LMs
    )

    def __str__(self) -> str:
        """Custom __str__ dunder method."""
        return self.stringify()

    def __setattr__(self, name, value):
        """
        Custom __setattr__ dunder method to prevent external contexts from setting attrs.
        """
        # Get the call stack
        stack = inspect.stack()
        # Check if the caller is a method of this class
        caller_frame = stack[1]
        caller_self = caller_frame.frame.f_locals.get("self", None)
        # Allow setting if called from an instance method of this class
        if caller_self is self and isinstance(caller_self, TaskNode):
            object.__setattr__(self, name, value)
        else:
            raise AttributeError(
                f"Cannot set '{name}' outside of class methods"
            )

    @property
    def next_planned_subtask(self) -> Optional["TaskNode"]:
        if not self.idx_of_next_planned_subtask < len(self.subtasks):
            raise ValueError(
                "OLTHAD corrupted: next planned subtask index out of `subtasks` bounds"
            )
        return self.subtasks[self.idx_of_next_planned_subtask]

    def stringify(
        self,
        indent: int = cfg.JSON_DUMPS_INDENT,
        # style: OlthadStringifyStyle = OlthadStringifyStyle.JSON,  # TODO: Implement this?
        redact_planned_subtasks_below: Optional[str] = None,
        obfuscate_status_of: Optional[str] = None,
    ) -> str:
        """
        Custom logic to get an LM-friendly string representation of a task node/OLTHAD.

        Args:
            indent (int): The number of spaces to indent each level of the task node.
            redact_planned_subtasks_below (Optional[str], optional): If provided, all
                planned subtasks below this task will be redacted. Defaults to None.
            obfuscate_status_of (Optional[str], optional): If provided, the status of the
                task with this description will be obfuscated. Defaults to None.
        """
        indent = " " * indent
        output_str = ""

        def increment_node_str_to_output_str(
            node: TaskNode,
            indent_lvl: int = 0,
            should_redact_planned: bool = False,
        ) -> str:
            nonlocal output_str

            ############################################################################
            ## Increment unclosed json dump w/out 'subtasks' & `DONT_STRINGIFY_ATTRS` ##
            ############################################################################

            partial_node_dict = {}
            for key, value in node.__dict__.items():
                if key == "subtasks" or key in TaskNode.DONT_STRINGIFY_ATTRS:
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
            to_append_to_output_str = ""
            for i, line in enumerate(lines):
                to_append_to_output_str += "\n" + (indent * indent_lvl + line)
            output_str += to_append_to_output_str + ",\n"

            ##################################################################
            ## Increment subtasks and close the node dict/object with a "}" ##
            ##################################################################

            # Check if we should redact this node's planned subtasks
            if (
                redact_planned_subtasks_below is not None
                and node.id == redact_planned_subtasks_below
            ):
                should_redact_planned = True

            if node.subtasks:
                # Open the subtasks list/array
                output_str += indent * (indent_lvl + 1) + '"subtasks": ['

                # Iterate through subtasks
                n_subtasks = len(node.subtasks)
                for i, subtask in enumerate(node.subtasks):

                    # Check if we've reached a planned subtask that should be redacted
                    if (
                        should_redact_planned
                        and subtask.status == TaskStatus.PLANNED
                    ):
                        # Redact from here on
                        output_str += "\n" + indent * (indent_lvl + 2)
                        output_str += TaskNode.REDACTED_PLANS_STR
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

                # Finally, close the subtasks list/array
                output_str += "\n" + indent * (indent_lvl + 1) + "]\n"

            else:
                output_str += indent * (indent_lvl + 1) + '"subtasks": null\n'

            # Close the node dict/object after incrementing subtasks
            output_str += indent * indent_lvl + "}"

        increment_node_str_to_output_str(self)
        return output_str

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
                "This method should only be called if the node is in-progress"
            )

        childless_copy_of_self = TaskNode(
            id=self.id,
            task=self.task,
            status=self.status,
            retrospective=self.retrospective,
            subtasks=[],
            parent_id=self.parent_id,
            idx_of_next_planned_subtask=self.idx_of_next_planned_subtask,
        )

        cur_in_progress_node_childless_copy = childless_copy_of_self
        cur_in_progress_node = self

        # Change name for readability since during rebuild it will get children
        root_of_rebuild = childless_copy_of_self

        while True:
            yield root_of_rebuild, cur_in_progress_node_childless_copy

            if len(cur_in_progress_node.subtasks) == 0:  # Rebuild complete
                break

            # Iterate through subtasks to both:
            # 1. Create childless copies of the subtasks
            # 2. Find the idx of the in-progress subtasks
            idx_of_in_progress_subtask = None
            for i, subtask in enumerate(cur_in_progress_node.subtasks):

                subtask_childless_copy = TaskNode(
                    id=subtask.id,
                    task=subtask.task,
                    status=subtask.status,
                    retrospective=subtask.retrospective,
                    subtasks=[],  # We never need subtasks beyond cur rebuild level
                )

                cur_in_progress_node_childless_copy.subtasks.append(
                    subtask_childless_copy
                )

                if subtask_childless_copy.status == TaskStatus.IN_PROGRESS:
                    idx_of_in_progress_subtask = i

            if idx_of_in_progress_subtask is None:
                raise ValueError(
                    f"OLTHAD corrupted: No in-progress status found amongst {i+1} "
                    "`subtasks` during call to `iter_in_progress_descendants`"
                )
            else:
                # Update `cur_in_progress_node` and `cur_in_progress_node_childless_copy`
                cur_in_progress_node = cur_in_progress_node.subtasks[
                    idx_of_in_progress_subtask
                ]
                cur_in_progress_node_childless_copy = (
                    cur_in_progress_node_childless_copy.subtasks[
                        idx_of_in_progress_subtask
                    ]
                )

    def replace_any_planned_subtasks_with(
        self, new_planned_subtasks: List["TaskNode"]
    ) -> None:
        """
        Replaces the planned subtasks (if any) of the node with the provided list of new
        planned subtasks.

        Args:
            new_planned_subtasks (List[TaskNode]): The new planned subtasks to replace
                the existing planned subtasks with.
        """

        # Verify inputs
        if not all(
            st.status == TaskStatus.PLANNED for st in new_planned_subtasks
        ):
            raise ValueError(
                "All new planned subtasks must have status `TaskStatus.PLANNED`"
            )
        if not all(st.parent_id == self.id for st in new_planned_subtasks):
            raise ValueError(
                f"All new planned subtasks must point to their parent: {self.id}"
            )

        # Update index of next planned subtask if necessary
        if self.idx_of_next_planned_subtask is None:
            if len(self.subtasks) > 0:
                raise ValueError(
                    "OLTHAD corrupted: `idx_of_next_planned_subtask` must be set if "
                    "there are planned subtasks"
                )
            self.idx_of_next_planned_subtask = 0

        # Plop these bad boys in there (replacing any planned ones)
        self.subtasks = (
            self.subtasks[: self.idx_of_next_planned_subtask]
            + new_planned_subtasks
        )

    def wipe_subtasks_list(self) -> None:
        """Prunes all subtasks below the current node."""
        self.subtasks = self.subtasks[: self.idx_of_next_planned_subtask]

    def update_status(self, new_status: TaskStatus) -> None:
        """
        Updates the status of the node.

        Args:
            new_status (TaskStatus): The new status to assign to the node.
        """
        self.status = new_status

    def update_retrospective(self, new_retrospective: str) -> None:
        """
        Updates the retrospective of the node.

        Args:
            new_retrospective (str): The new retrospective to assign to the node.
        """
        self.retrospective = new_retrospective
