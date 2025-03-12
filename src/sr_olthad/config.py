from enums import SerializationMethod

STRINGIFY_ENV_STATE_SERIALIZATION_METHOD: SerializationMethod = SerializationMethod.YAML


class MaxValidOutputTries:
    """Max tries to get a valid output for sr-OLTHAD `InstructLmAgents`."""

    # Attempt summarizer
    ATTEMPT_SUMMARIZER: int = 3
    # Backtracker
    EXHAUSTIVE_EFFORT_CLF: int = 2
    MOST_WORTHWHILE_PURSUIT_CLF: int = 2
    PARTIAL_SUCCESS_CLF: int = 2
    SUCCESSFUL_COMPLETION_CLF: int = 2
    # Forgetter
    FORGETTER: int = 2
    # Planner
    PLANNER: int = 2


class PromptVersions:
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
