from typing import ClassVar

from jinja2 import Template
from pydantic import BaseModel, Field

from sr_olthad.framework.utils import get_prompt_json_spec
from sr_olthad.prompts._strings import (
    EXAMPLE_OLTHAD_FOR_SYS_PROMPT,
    EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT,
)
from sr_olthad.schema import (
    DomainSpecificSysPromptInputFields,
    PromptRegistry,
    SingleTurnPromptTemplates,
    UserPromptInputFields,
)


class PlannerLmResponseOutputData(BaseModel):
    """
    Data to be parsed from the LM's response within the Planner.

    Attributes:
        new_planned_subtasks (list[str]): The new set of planned subtasks for the node
            in question.
    """

    # NOTE: These must correspond to the field attrs below.
    new_planned_subtasks_attr: ClassVar[str] = "new_planned_subtasks"

    # Fields
    new_planned_subtasks: list[str] = Field(
        description="The new set of planned subtasks for the node in question.",
        field_type="list[str]",
    )


######################
######## v1.0 ########
######################

SYS_1_0 = f"""You are a helpful AI agent who plays a crucial role in a hierarchical reasoning and acting system. Your specific job is to create and update tentative plans at a conservative next-most-logical level of granularity.

You will be given:

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
TASK IN QUESTION:
{EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT}
```

Regardless of whether the task in question has tentatively planned subtasks, your job is to consider how things are progressing (with respect to the aims/plans towards parent outcomes) and provide an updated set of tentatively planned subtasks for the task in question. This, your updated set will replace any existing tentatively planned subtasks. Therefore, e.g., if the existing tentatively planned subtasks are fine as-is, simply list them back and they will be fed back into system with no change.

Since the system is designed to gradually break down tasks as much as needed, you should not over-granularize the planned subtasks too early. Instead focus on planning at a sensible next-most level of abstraction that will help define crucial task-concepts without planning forward too much detail. After all, the future is often uncertain and it would inefficient to speculate too granularly too far into the future. When planning at high levels of abstraction, focus on crucial strategic steps that will roughly outline good strategies. Then, when planning at lower levels of abstraction, you'll have enough strategical context to inform more detailed steps. Focus intently on conforming your plans to be intelligent given what you are observing in the environment. Think about past retrospectives and try not to fall into the same repetitive patterns or repeat futile actions/strategies.

Carefully think step-by-step. Finally, only once you've concluded your deliberation, provide your final response in a JSON that strictly adheres to the following format:

```json
{get_prompt_json_spec(PlannerLmResponseOutputData)}
```

{{{{ {DomainSpecificSysPromptInputFields.DOMAIN_EXPOSITION} }}}}"""

USER_1_0 = f"""CURRENT ACTOR/ENVIRONMENT STATE:
```text
{{{{ {UserPromptInputFields.ENV_STATE} }}}}
```

PROGRESS/PLANS:
```json
{{{{ {UserPromptInputFields.OLTHAD} }}}}
```

TASK IN QUESTION:
```json
{{{{ {UserPromptInputFields.TASK_IN_QUESTION} }}}}
```
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
