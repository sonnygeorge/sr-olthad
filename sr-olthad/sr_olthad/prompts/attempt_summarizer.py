from typing import ClassVar

from jinja2 import Template
from pydantic import BaseModel, Field

from sr_olthad.framework.utils import get_prompt_json_spec
from sr_olthad.prompts._strings import (
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
        json_schema_extra={"field_type": "str"},
    )
    retrospective_to_assign: str = Field(
        description="The retrospective to assign to the attempted subtask.",
        json_schema_extra={"field_type": "str"},
    )


######################
######## v1.0 ########
######################

V1_0_QUESTION = "Which status is the most appropriate to assign and why?"

SYS_1_0 = f"""You are a helpful thinking assistant that {{{{ {DomainSpecificSysPromptInputFields.LM_ROLE_AS_VERB_PHRASE} }}}}. Your specific job is to reflect over the environment state to decide how successful a recently attempted skill (task) seems to have been and produce a summative retrospective account of the attempt, making sure to include any details that could be useful to remember in the future.

## Your Inputs

You will be provided:

1. CURRENT ENVIRONMENT STATE: a representation of the most recently observed state of the environment you are in.
2. PROGRESS/PLANS: a JSON depicting your ongoing progress and hierarchical plans, where the root task is your overall goal.
3. ATTEMPTED TASK IN QUESTION: a JSON object defining the task you are evaluating the completion of. Please note that the `status` of your "task in question" will be a question mark since you are evaluating it. E.g.,
```text
ATTEMPTED TASK IN QUESTION:
{EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT}
```
4. QUESTION: The question you are to answer.

## Your Response

Think step-by-step before providing your final response to the QUESTION.

!IMPORTANT:
- Look for evidence of the attempt's in the environment state and not the progress/plans.
- Only refer to the plans to consider the greater context for what were the intentions of this attempt.

Only after expounding your reasoning process, you will output your final answer as a JSON that strictly adheres to this specification:

```json
{get_prompt_json_spec(AttemptSummarizerLmResponseOutputData)}
```

The attempt statuses you can assign are limited to: "{AttemptedTaskStatus.SUCCESS}", "{AttemptedTaskStatus.PARTIAL_SUCCESS}", or "{AttemptedTaskStatus.FAILURE}".

## Auxiliary Information About Domain

{{{{ {DomainSpecificSysPromptInputFields.DOMAIN_EXPOSITION} }}}}"""

USER_1_0 = f"""CURRENT ENVIRONMENT STATE:
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
