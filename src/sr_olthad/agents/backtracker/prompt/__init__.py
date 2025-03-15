from sr_olthad.agents.backtracker.prompt.common import (
    BacktrackerSubAgentInputPromptData,
    BacktrackerSubAgentOutputPromptData,
    BacktrackerSubAgentOutputFields,
)
from sr_olthad.agents.backtracker.prompt.exhaustive_effort import (
    PROMPT_REGISTRY as EXHAUSTIVE_EFFORT_CLF_PROMPT_REGISTRY,
    EFFORT_WAS_EXHAUSTIVE_OPTIONS,
)
from sr_olthad.agents.backtracker.prompt.most_worthwhile_pursuit import (
    PROMPT_REGISTRY as MOST_WORTHWHILE_PURSUIT_CLF_PROMPT_REGISTRY,
    IS_MOST_WORTHWHILE_OPTIONS,
)
from sr_olthad.agents.backtracker.prompt.partial_success import (
    PROMPT_REGISTRY as PARTIAL_SUCCESS_CLF_PROMPT_REGISTRY,
    WAS_PARTIAL_SUCCESS_OPTIONS,
)
from sr_olthad.agents.backtracker.prompt.successful_completion import (
    PROMPT_REGISTRY as SUCCESSFUL_COMPLETION_CLF_PROMPT_REGISTRY,
    WAS_SUCCESSFULLY_COMPLETED_OPTIONS,
)
