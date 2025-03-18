from abc import ABC
from typing import List

from pydantic import BaseModel

from agent_framework.schema import InstructLmMessage
from sr_olthad.task_node import TaskNode


class InferenceStepEmission(BaseModel):
    """Data emitted by sr-OLTHAD after every step of inference."""

    agent_name: str
    current_olthad: TaskNode
    pending_olthad: TaskNode
    messages: List[InstructLmMessage] | List[List[InstructLmMessage]]


class InferenceStepHandler(ABC):
    """
    Callable that handles `StepEmissioData` and returns whether to accept the step
    emission or force a re-run.

    Args:
        step_emission: Data emitted by sr-OLTHAD after every step of inference.

    Returns:
        bool: Whether to accept the step emission or force a re-run.
    """

    def __call__(self, step_emission: InferenceStepEmission) -> bool:
        # Do whatever w/ data
        pass
