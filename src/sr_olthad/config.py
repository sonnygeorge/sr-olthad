"""Single location for tweakable hyperparameters for the sr-OLTHAD system.

TODO: Make the UX more like hunggingface's `TrainingArguments` class & make generally
sensible static values like these be the default values.
"""

from enums import SerializationMethod

from instruct_lms import OpenAIInstructLm
from schema import InstructLm

from sr_olthad.agents.attempt_summarizer import ATTMPT_SMMRZR_PROMPT_REGISTRY
from sr_olthad.agents.backtracker import (
    EXHSTVE_EFFRT_PROMPT_REGISTRY,
    WRTHWHL_PURST_PROMPT_REGISTRY,
    PRTL_SCCSS_PROMPT_REGISTRY,
    SCCSS_CMPLTN_PROMPT_REGISTRY,
)
from sr_olthad.agents.forgetter import FRGTTR_PROMPT_REGISTRY
from sr_olthad.agents.planner import PLNNR_PROMPT_REGISTRY


STRINGIFY_ENV_STATE_SERIALIZATION_METHOD: SerializationMethod = SerializationMethod.YAML


class MaxValidOutputTries:
    """Max tries to get a valid output for sr-OLTHAD `InstructLmAgents`."""

    # Attempt summarizer
    ATTEMPT_SUMMARIZER: int = 2
    # Backtracker
    EXHAUSTIVE_EFFORT_CLF: int = 2
    MOST_WORTHWHILE_PURSUIT_CLF: int = 2
    PARTIAL_SUCCESS_CLF: int = 2
    SUCCESSFUL_COMPLETION_CLF: int = 2
    # Forgetter
    FORGETTER: int = 2
    # Planner
    PLANNER: int = 2


class AgentPromptVersions:
    """Prompt versions to use for sr-OLTHAD `InstructLmAgents`."""

    # Attempt summarizer
    ATTEMPT_SUMMARIZER: str = "1.0"
    # Backtracker
    EXHAUSTIVE_EFFORT_CLF: str = "1.0"
    MOST_WORTHWHILE_PURSUIT_CLF: str = "1.0"
    PARTIAL_SUCCESS_CLF: str = "1.0"
    SUCCESSFUL_COMPLETION_CLF: str = "1.0"
    # Forgetter
    FORGETTER: str = "1.0"
    # Planner
    PLANNER: str = "1.0"


class AgentInstructLms:
    """`InstructLm`s to use for sr-OLTHAD `InstructLmAgents`."""

    # Attempt summarizer
    ATTEMPT_SUMMARIZER: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
    # Backtracker
    EXHAUSTIVE_EFFORT_CLF: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
    MOST_WORTHWHILE_PURSUIT_CLF: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
    PARTIAL_SUCCESS_CLF: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
    SUCCESSFUL_COMPLETION_CLF: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
    # Forgetter
    FORGETTER: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")
    # Planner
    PLANNER: InstructLm = OpenAIInstructLm(model="gpt-3.5-turbo")


class AgentPrompts:
    """Prompts to use for sr-OLTHAD `InstructLmAgents`."""

    # Attempt summarizer
    ATTEMPT_SUMMARIZER = ATTMPT_SMMRZR_PROMPT_REGISTRY[
        AgentPromptVersions.ATTEMPT_SUMMARIZER
    ]
    # Backtracker
    EXHAUSTIVE_EFFORT_CLF = EXHSTVE_EFFRT_PROMPT_REGISTRY[
        AgentPromptVersions.EXHAUSTIVE_EFFORT_CLF
    ]
    MOST_WORTHWHILE_PURSUIT_CLF = WRTHWHL_PURST_PROMPT_REGISTRY[
        AgentPromptVersions.MOST_WORTHWHILE_PURSUIT_CLF
    ]
    PARTIAL_SUCCESS_CLF = PRTL_SCCSS_PROMPT_REGISTRY[
        AgentPromptVersions.PARTIAL_SUCCESS_CLF
    ]
    SUCCESSFUL_COMPLETION_CLF = SCCSS_CMPLTN_PROMPT_REGISTRY[
        AgentPromptVersions.SUCCESSFUL_COMPLETION_CLF
    ]
    # Forgetter
    FORGETTER = FRGTTR_PROMPT_REGISTRY[AgentPromptVersions.FORGETTER]
    # Planner
    PLANNER = PLNNR_PROMPT_REGISTRY[AgentPromptVersions.PLANNER]
