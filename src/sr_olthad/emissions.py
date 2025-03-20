from typing import List, Protocol

from pydantic import BaseModel

from agent_framework.schema import InstructLmMessage, PotentiallyNestedInstructLmMessages
from sr_olthad.schema import AgentName


class PreLmGenerationStepEmission(BaseModel):
    agent_name: AgentName
    cur_node_id: str
    prompt_messages: List[InstructLmMessage]
    n_streams_to_handle: int = 1


class PostLmGenerationStepEmission(BaseModel):
    # TODO: Change - the exhaustive effort classifier never outputs a diff
    diff: List[str]
    full_messages: PotentiallyNestedInstructLmMessages


class PreLmGenerationStepHandler(Protocol):
    """
    Callable that handles a `PreLmGenerationStepEmission` and returns whether to accept
    the olthad update or force a re-run of the LM generation step.

    Args:
        emission (PreLmGenerationStepEmission): Emission data.
    Returns:
        bool: Whether to accept the step emission or force a re-run.
    """

    def __call__(self, emission: PreLmGenerationStepEmission) -> bool:
        pass


class PostLmGenerationStepHandlerAndApprover(Protocol):
    """
    Callable that handles a `PostLmGenerationStepEmission` and returns whether to "approve"
    the LM generation step or force a re-run of the LM generation step.

    Args:
        emission (PostLmGenerationStepEmission): Emission data.
    Returns:
        bool: Whether to accept the step emission or force a re-run.
    """

    def __call__(self, emission: PostLmGenerationStepEmission) -> bool:
        pass
