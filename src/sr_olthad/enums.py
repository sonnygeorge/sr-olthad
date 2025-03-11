from enum import StrEnum


class AttemptedTaskStatus(StrEnum):
    IN_PROGRESS = "In progress"
    SUCCESS = "Attempted (success)"
    PARTIAL_SUCCESS = "Attempted (partial success)"


class BacktrackedFromTaskStatus(AttemptedTaskStatus):
    DROPPED = "Dropped"


class TaskStatus(BacktrackedFromTaskStatus):
    PLANNED = "Tentatively planned"
