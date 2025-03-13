from typing import Generator, List, Optional, Tuple

from pydantic import BaseModel

import sr_olthad.config as cfg
from sr_olthad.enums import TaskStatus
from utils import StructuredDataStringifier


class TaskNode(BaseModel):  # I.e., an OLTHAD
    task: str
    description: str
    status: TaskStatus
    retrospective: Optional[str] = None
    subtasks: Optional[List["TaskNode"]] = None

    def iter_in_progress_descendants(
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
        as_dict = self.model_dump()
        return StructuredDataStringifier.stringify(
            as_dict, serialization_method=cfg.STRINGIFY_OLTHAD_SERIALIZATION_METHOD
        )
