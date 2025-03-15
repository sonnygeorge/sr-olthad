import json
from typing import Generator, List, Optional, Tuple

from pydantic import BaseModel

from sr_olthad.config import OlthadCfg as cfg
from sr_olthad.olthad.task_status import TaskStatus


class TaskNode(BaseModel):  # (I.e., an OLTHAD)
    task: str
    description: str
    status: TaskStatus
    retrospective: Optional[str] = None
    subtasks: Optional[List["TaskNode"]] = None

    def iter_in_progress_descendants(  # TODO: Docstring!
        self,
    ) -> Generator[Tuple["TaskNode", "TaskNode"], None, None]:
        if self.status != TaskStatus.IN_PROGRESS:
            raise ValueError(
                "This method should only be called if the node is in-progress"
            )

        rebuild_root = TaskNode(
            task=self.task,
            description=self.description,
            status=self.status,
            retrospective=self.retrospective,
            subtasks=None,
        )

        cur_rebuild_node = rebuild_root
        cur_self_node = self
        while True:
            yield rebuild_root, cur_rebuild_node
            cur_rebuild_node.subtasks = []
            idx_of_in_progress_subtask = None
            for i, subtask in enumerate(cur_self_node.subtasks):
                rebuilt_subtask = TaskNode(
                    task=subtask.task,
                    description=subtask.description,
                    status=subtask.status,
                    retrospective=subtask.retrospective,
                    subtasks=None,
                )
                cur_rebuild_node.subtasks.append(rebuilt_subtask)

                if rebuilt_subtask.status == TaskStatus.IN_PROGRESS:
                    idx_of_in_progress_subtask = i

            if idx_of_in_progress_subtask is None:
                break
            else:
                cur_self_node = cur_self_node.subtasks[idx_of_in_progress_subtask]
                cur_rebuild_node = cur_rebuild_node.subtasks[idx_of_in_progress_subtask]

    def __str__(self) -> str:
        return self.stringify()

    def stringify(
        self,
        indent: int = cfg.JSON_DUMPS_INDENT,
        # style: OlthadStringifyStyle = OlthadStringifyStyle.JSON,  # TODO: Implement this
        redact_planned_subtasks_below: Optional[str] = None,
        obfuscate_status_of: Optional[str] = None,
    ) -> str:
        """
        Gets an LM-friendly string representation of a task node/OLTHAD.

        Args:
            indent (int): The number of spaces to indent each level of the task node.
            redact_planned_subtasks_below (Optional[str], optional): If provided, all
                planned subtasks below this task will be redacted. Defaults to None.
            obfuscate_status_of (Optional[str], optional): If provided, the status of the
                task with this description will be obfuscated. Defaults to None.
        """
        # TODO: Put these constants somewhere else?
        redacted_str = "(FUTURE PLANNED TASKS REDACTED)"
        obfuscated_status_str = "?"

        indent = " " * indent
        output_str = ""

        def increment_partial_node_str(node: TaskNode, indent_lvl: int) -> str:
            nonlocal output_str
            partial_node_dict = {}
            for key, value in node.__dict__.items():
                if key == "subtasks":
                    continue
                if (
                    obfuscate_status_of is not None
                    and key == "status"
                    and node.task == obfuscate_status_of
                ):
                    value = obfuscated_status_str
                partial_node_dict[key] = value
            partial_node_str = json.dumps(partial_node_dict, indent=indent)
            lines = partial_node_str[:-2].split("\n")
            to_append_to_output_str = ""
            for i, line in enumerate(lines):
                to_append_to_output_str += "\n" + (indent * indent_lvl + line)
            output_str += to_append_to_output_str + ",\n"

        def process_node(
            node: TaskNode, indent_lvl: int = 0, should_redact_planned: bool = False
        ) -> str:
            nonlocal output_str
            increment_partial_node_str(node, indent_lvl)
            if (
                redact_planned_subtasks_below is not None
                and node.task == redact_planned_subtasks_below
            ):
                should_redact_planned = True
            if node.subtasks:
                # Open the subtasks list/array
                output_str += indent * (indent_lvl + 1) + '"subtasks": ['
                n_subtasks = len(node.subtasks)
                for i, subtask in enumerate(node.subtasks):
                    if should_redact_planned and subtask.status == TaskStatus.PLANNED:
                        output_str += "\n" + indent * (indent_lvl + 2)
                        output_str += redacted_str
                        break
                    process_node(subtask, indent_lvl + 2, should_redact_planned)
                    if i < n_subtasks - 1:
                        output_str += ","
                # Close the subtasks list/array
                output_str += "\n" + indent * (indent_lvl + 1) + "]\n"
                output_str += indent * indent_lvl + "}"  # Close the node dict/object
            else:
                output_str += indent * (indent_lvl + 1) + '"subtasks": null\n'
                output_str += indent * indent_lvl + "}"  # Close the node dict/object

        process_node(self)
        return output_str
