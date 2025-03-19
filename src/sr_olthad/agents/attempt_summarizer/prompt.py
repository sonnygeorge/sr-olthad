from enum import StrEnum

from jinja2 import Template
from pydantic import BaseModel

from sr_olthad.agents.prompt import (
    EXAMPLE_OLTHAD_FOR_SYS_PROMPT,
    EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT,
)
from sr_olthad.olthad import AttemptedTaskStatus
from sr_olthad.schema import PromptRegistry, SingleTurnPromptTemplates


class AttemptSummarizerPromptInputData(BaseModel):
    """
    Input data for the Attempt Summarizer agent.

    Attributes:
        env_state (str): PRE-STRINGIFIED current environment state.
        root_task_node (str): PRE-STRINGIFIED root task node of the OLTHAD.
        attempted_subtask_node (str): PRE-STRINGIFIED subtask node whose attempt we
            want to summarize.
    """

    env_state: str
    olthad: str
    attempted_subtask_node: str


class AttemptSummarizerInputFields(StrEnum):
    ENV_STATE = "env_state"
    OLTHAD = "olthad"
    ATTEMPTED_SUBTASK_NODE = "attempted_subtask_node"


class AttemptSummarizerLmResponseOutputData(BaseModel):
    """
    Output data for the Attempt Summarizer agent.

    Attributes:
        status_to_assign (AttemptedTaskStatus): The status to assign to the attempted subtask.
        retrospective_to_assign (str): The retrospective to assign to the attempted
            subtask.
    """

    status_to_assign: AttemptedTaskStatus
    retrospective_to_assign: str


class AttemptSummarizerOutputFields(StrEnum):
    STATUS_TO_ASSIGN = "status_to_assign"
    RETROSPECTIVE_TO_ASSIGN = "retrospective_to_assign"


JSON_FORMAT_SYS_PROMPT_INSERT = f"""{{
    "{AttemptSummarizerOutputFields.STATUS_TO_ASSIGN}": "(str) The status to assign to the attempted subtask.",
    "{AttemptSummarizerOutputFields.RETROSPECTIVE_TO_ASSIGN}": "(str) The retrospective to assign to the attempted subtask.",
}}"""


######################
######## v1.0 ########
######################

V1_0_QUESTION = "Which status is the most appropriate to assign and why?"

SYS_1_0 = f"""You are a helpful AI agent who plays a crucial role in a hierarchical reasoning and acting system.

Your specific job is to reflect over the environment state to decide how successful a just-finished task-attempt seems to have been and commit a summative retrospective account containing any reflections about how things seems to have transpired, making sure to include all such details that could be useful to have registered in the future.

The attempt statuses you can assign are limited to: "{AttemptedTaskStatus.SUCCESS}", "{AttemptedTaskStatus.PARTIAL_SUCCESS}", or "{AttemptedTaskStatus.FAILURE}".

First, you will be given:

1. Information representing/describing the current, up-to-date state of the environment:

```text
CURRENT ACTOR/ENVIRONMENT STATE:
...
```

2. A representation of the ongoing progress/plans, e.g.:

```text
PROGRESS/PLANS:
{EXAMPLE_OLTHAD_FOR_SYS_PROMPT}
```

3. Followed by an indication of which in-progress task about which you will be questioned, e.g.:

```text
ATTEMPTED TASK IN QUESTION:
{EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT}
```

The you

{V1_0_QUESTION}

Finally, you will be prompted to to think step-by-step before providing your final response to the question, "{V1_0_QUESTION}".

!IMPORTANT:
- Look for evidence of the attempt's in the environment state and not the progress/plans.
- Only refer to the plans to consider the greater context for what where the intentions of this attempt.

Only after thinking it through, you will respond in a JSON that strictly adheres to the following format:

```json
{JSON_FORMAT_SYS_PROMPT_INSERT}
```"""

USER_1_0 = f"""CURRENT ACTOR/ENVIRONMENT STATE:
```text
{{{{ {AttemptSummarizerInputFields.ENV_STATE} }}}}
```

PROGRESS/PLANS:
```json
{{{{ {AttemptSummarizerInputFields.OLTHAD} }}}}
```

ATTEMPTED TASK IN QUESTION:
```json
{{{{ {AttemptSummarizerInputFields.ATTEMPTED_SUBTASK_NODE} }}}}
```

{V1_0_QUESTION}

Please think carefully step-by-step before providing your final response.
"""

V1_0_PROMPTS = SingleTurnPromptTemplates(
    sys_prompt_template=Template(SYS_1_0),
    user_prompt_template=Template(USER_1_0),
)

V1_0_PROMPTS = SingleTurnPromptTemplates(
    sys_prompt_template=Template(SYS_1_0),
    user_prompt_template=Template(USER_1_0),
)

######################
###### Registry ######
######################

PROMPT_REGISTRY: PromptRegistry = {
    "1.0": V1_0_PROMPTS,
}
