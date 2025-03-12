from dataclasses import dataclass
from typing import Dict, List, Optional

from pydantic import BaseModel

from sr_olthad.enums import AttemptedTaskStatus, BacktrackedFromTaskStatus, TaskStatus


class TaskNode(BaseModel):
    task: str
    description: str
    status: TaskStatus
    retrospective: Optional[str] = None
    subtasks: Optional[List["TaskNode"]] = None


@dataclass
class OlthadTraversal:
    # TODO: Docstrings, unit tests, & update(s) used after the forgetter is called
    # TODO: Could this be made marginally cleaner by having `TaskNode`s have their own
    # next_planned_subtask_idx attr, but never printing it?
    # (I think this makes other code non-trivially messier unless I KNOW I want to write
    # custom stringification logic for `TaskNode`s)

    def __init__(self, task_description: str):
        self.root_node: TaskNode = TaskNode(
            task="1",
            description=task_description,
            status=TaskStatus.IN_PROGRESS,
        )
        self.cur_node: TaskNode = self.root_node
        self._nodes: Dict[str, TaskNode] = {self.root_node.task: self.root_node}
        self._next_planned_subtask_idxs: Dict[str, int] = {self.root_node.task: 0}

    @property
    def next_planned_subtask_of_cur_node(self) -> Optional[TaskNode]:
        if self.cur_node.subtasks is None:
            return None
        next_planned_subtask_idx = self._next_planned_subtask_idxs[self.cur_node.task]
        return self.cur_node.subtasks[next_planned_subtask_idx]

    def update_next_planned_subtask_after_attempt(
        self, status: AttemptedTaskStatus, retrospective: Optional[str] = None
    ) -> None:
        # Get the attempted subtask (the next-most planned subtask)
        # NOTE: cur_node should always be in this dict
        attempted_subtask_idx = self._next_planned_subtask_idxs[self.cur_node.task]
        # NOTE: subtasks should never be None
        attempted_subtask = self.cur_node.subtasks[attempted_subtask_idx]
        # Update the status and retrospective of the attempted subtask
        attempted_subtask.status = status
        attempted_subtask.retrospective = retrospective
        # Increment the next-most planned subtask index
        self._next_planned_subtask_idxs[self.cur_node.task] += 1

    def update_planned_subtasks(self, new_planned_subtasks: List[TaskNode]) -> None:
        # Remove existing planned subtask nodes
        if self.cur_node.task not in self._next_planned_subtask_idxs:
            assert self.cur_node.subtasks is None  # These conditions should be in sync
        else:
            next_planned_subtask_idx = self._next_planned_subtask_idxs[
                self.cur_node.task
            ]
            for subtask in self.cur_node.subtasks[next_planned_subtask_idx:]:
                del self._nodes[subtask.task]
                del self._next_planned_subtask_idxs[subtask.task]
            self.cur_node.subtasks = self.cur_node.subtasks[:next_planned_subtask_idx]
        # Add new planned subtask nodes
        if self.cur_node.subtasks is None:
            self.cur_node.subtasks = new_planned_subtasks
            self._next_planned_subtask_idxs[self.cur_node.task] = 0
        else:
            self.cur_node.subtasks.extend(new_planned_subtasks)
        for subtask in new_planned_subtasks:
            self._nodes[subtask.task] = subtask

    def backtrack(
        self,
        status: BacktrackedFromTaskStatus,
        retrospective: str,
        prune_subtasks: bool,
    ) -> None:
        # Update the status and retrospective of the current node
        self.cur_node.status = status
        self.cur_node.retrospective = retrospective
        # Prune subtasks
        if prune_subtasks is True and self.cur_node.subtasks is not None:
            for subtask in self.cur_node.subtasks:
                del self._nodes[subtask.task]
                del self._next_planned_subtask_idxs[subtask.task]
            self.cur_node.subtasks = None
        # Move cur_node to its parent
        self.cur_node = self._nodes[self.cur_node.task[:-1]]

    def recurse_inward(self) -> None:
        # Get the next-most planned subtask
        next_planned_subtask_idx = self._next_planned_subtask_idxs[self.cur_node.task]
        next_planned_subtask = self.cur_node.subtasks[next_planned_subtask_idx]
        # Move cur_node to the next-most planned subtask
        self.cur_node = next_planned_subtask
