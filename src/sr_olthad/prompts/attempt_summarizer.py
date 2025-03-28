from typing import ClassVar

from jinja2 import Template
from pydantic import BaseModel, Field

from common.utils import get_prompt_json_spec
from sr_olthad.prompts._strings import (
    EXAMPLE_OLTHAD_FOR_SYS_PROMPT,
    EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT,
)
from sr_olthad.schema import (
    AttemptedTaskStatus,
    CommonSysPromptInputFields,
    CommonUserPromptInputFields,
    PromptRegistry,
    SingleTurnPromptTemplates,
)


class AttemptSummarizerLmResponseOutputData(BaseModel):
    """
    Output data for the Attempt Summarizer agent.

    Attributes:
        status_to_assign (AttemptedTaskStatus): The status to assign to the attempted subtask.
        retrospective_to_assign (str): The retrospective to assign to the attempted
            subtask.
    """

    # NOTE: These must correspond to the field attrs below.
    status_attr: ClassVar[str] = "status_to_assign"
    retrospective_attr: ClassVar[str] = "retrospective_to_assign"

    # Fields
    status_to_assign: AttemptedTaskStatus = Field(
        description="The status to assign to the attempted subtask.",
        field_type="str",
    )
    retrospective_to_assign: str = Field(
        description="The retrospective to assign to the attempted subtask.",
        field_type="str",
    )


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

Then, you will be asked:

{V1_0_QUESTION}

Finally, you will be prompted to to think step-by-step before providing your final response to the question, "{V1_0_QUESTION}".

!IMPORTANT:
- Look for evidence of the attempt's in the environment state and not the progress/plans.
- Only refer to the plans to consider the greater context for what where the intentions of this attempt.

Only after thinking it through, you will respond in a JSON that strictly adheres to the following format:

```json
{get_prompt_json_spec(AttemptSummarizerLmResponseOutputData)}
```

{{{{ {CommonSysPromptInputFields.DOMAIN_SPECIFIC_INSERT} }}}}"""

USER_1_0 = f"""CURRENT ACTOR/ENVIRONMENT STATE:
```text
{{{{ {CommonUserPromptInputFields.ENV_STATE} }}}}
```

PROGRESS/PLANS:
```json
{{{{ {CommonUserPromptInputFields.OLTHAD} }}}}
```

ATTEMPTED TASK IN QUESTION:
```json
{{{{ {CommonUserPromptInputFields.TASK_IN_QUESTION} }}}}
```

{V1_0_QUESTION}

Please think carefully step-by-step before providing your final response.
"""

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
