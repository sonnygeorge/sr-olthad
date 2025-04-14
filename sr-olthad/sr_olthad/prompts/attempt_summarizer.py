from typing import ClassVar

from jinja2 import Template
from pydantic import BaseModel, Field

from sr_olthad.framework.utils import get_prompt_json_spec
from sr_olthad.prompts._strings import (
    EXAMPLE_OLTHAD_FOR_SYS_PROMPT,
    EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT,
)
from sr_olthad.schema import (
    AttemptedTaskStatus,
    DomainSpecificSysPromptInputFields,
    PromptRegistry,
    SingleTurnPromptTemplates,
    UserPromptInputFields,
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

SYS_1_0 = f"""You are a helpful thinking assistant that {{{{ {DomainSpecificSysPromptInputFields.LM_ROLE_AS_VERB_PHRASE} }}}}. Your specific job is to reflect over the environment state to decide how successful a just-finished skill (task) attempt seems to have been and commit a summative retrospective account containing any reflections about how things seems to have transpired, making sure to include all such details that could be useful to remember in the future.

The attempt statuses you can assign are limited to: "{AttemptedTaskStatus.SUCCESS}", "{AttemptedTaskStatus.PARTIAL_SUCCESS}", or "{AttemptedTaskStatus.FAILURE}".

### Your Inputs

You will be provided:

1. A representation of the most recently observed state of the world (i.e., the environment you are in).
CURRENT ENVIRONMENT STATE:
...

2. A JSON depicting your ongoing progress (memory) and ever-evolving hierarchical plans, where the highest-most (root) task is requested of you by a human user. E.g.:
PROGRESS/PLANS:
```json
{EXAMPLE_OLTHAD_FOR_SYS_PROMPT}
```

3. An indication of the "attempted task in question" (i.e., the task for which you will be determining appropriate planned subtasks). E.g.:
```text
ATTEMPTED TASK IN QUESTION:
{EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT}
```

4. The question you are being asked:
QUESTION:
{V1_0_QUESTION}

### Your Response

Finally, you will think and reason step-by-step before providing your final response to the question.

!IMPORTANT:
- Look for evidence of the attempt's in the environment state and not the progress/plans.
- Only refer to the plans to consider the greater context for what where the intentions of this attempt.

Only after expounding your reasoning process, you will output your final answer as a JSON that strictly adheres to this specification:

```json
{get_prompt_json_spec(AttemptSummarizerLmResponseOutputData)}
```

### Potentially Useful Auxiliary Information About Domain

{{{{ {DomainSpecificSysPromptInputFields.DOMAIN_EXPOSITION} }}}}"""

USER_1_0 = f"""CURRENT ACTOR/ENVIRONMENT STATE:
```text
{{{{ {UserPromptInputFields.ENV_STATE} }}}}
```

PROGRESS/PLANS:
```json
{{{{ {UserPromptInputFields.OLTHAD} }}}}
```

ATTEMPTED TASK IN QUESTION:
```json
{{{{ {UserPromptInputFields.TASK_IN_QUESTION} }}}}
```

QUESTION:
{V1_0_QUESTION}"""

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
