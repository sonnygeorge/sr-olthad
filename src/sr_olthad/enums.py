from enum import StrEnum


class AttemptedTaskStatus(StrEnum):
    IN_PROGRESS = "In progress"
    SUCCESS = "Attempted (success)"
    PARTIAL_SUCCESS = "Attempted (partial success)"


class BacktrackedFromTaskStatus(StrEnum):
    IN_PROGRESS = AttemptedTaskStatus.IN_PROGRESS
    SUCCESS = AttemptedTaskStatus.SUCCESS
    PARTIAL_SUCCESS = AttemptedTaskStatus.PARTIAL_SUCCESS
    DROPPED = "Dropped"


class TaskStatus(StrEnum):
    IN_PROGRESS = AttemptedTaskStatus.IN_PROGRESS
    SUCCESS = AttemptedTaskStatus.SUCCESS
    PARTIAL_SUCCESS = AttemptedTaskStatus.PARTIAL_SUCCESS
    DROPPED = BacktrackedFromTaskStatus.DROPPED
    PLANNED = "Tentatively planned"
