from jinja2 import Template

from sr_olthad.agents.backtracker.prompt.common import (
    JSON_FORMAT_SYS_PROMPT_INSERT,
    BacktrackerSubAgentInputFields,
)
from sr_olthad.agents.prompt import (
    EXAMPLE_OLTHAD_FOR_SYS_PROMPT,
    EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT,
)
from sr_olthad.olthad import TaskStatus
from sr_olthad.schema import (
    MultipleChoiceQuestionOption,
    PromptRegistry,
    SingleTurnPromptTemplates,
)
from sr_olthad.utils import BinaryChoiceOptions

WAS_SUCCESSFULLY_COMPLETED_OPTIONS: BinaryChoiceOptions = {
    True: MultipleChoiceQuestionOption(
        letter="A",
        text="It can be said with confidence that the task has now been successfully completed.",
    ),
    False: MultipleChoiceQuestionOption(
        letter="B",
        text="What the task is aiming to achieve has not yet been fully realized.",
    ),
}


######################
######## v1.0 ########
######################


V1_0_QUESTION = "Can the task in question be considered done? I.e., which statement is more true?"

SYS_1_0 = f"""You are a helpful AI agent who plays a crucial role in a hierarchical reasoning and acting system. Your specific job is as follows.

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

3. Followed by an indication of which in-progress task to which you will consider assigning the "{TaskStatus.SUCCESS}" status. E.g.,:

```text
TASK IN QUESTION:
{EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT}
```

Finally, you will be asked the following:

{V1_0_QUESTION}
{WAS_SUCCESSFULLY_COMPLETED_OPTIONS[True].letter}. {WAS_SUCCESSFULLY_COMPLETED_OPTIONS[True].text}
{WAS_SUCCESSFULLY_COMPLETED_OPTIONS[False].letter}. {WAS_SUCCESSFULLY_COMPLETED_OPTIONS[False].text}

You will answer by first carefully thinking things through step-by-step. Only after you've thoroughly reasoned through things, provide a BRIEF final response in a JSON that strictly adheres to the following format:

```json
{JSON_FORMAT_SYS_PROMPT_INSERT}
```"""

USER_1_0 = f"""CURRENT ACTOR/ENVIRONMENT STATE:
```text
{{{{ {BacktrackerSubAgentInputFields.ENV_STATE} }}}}
```

PROGRESS/PLANS:
```json
{{{{ {BacktrackerSubAgentInputFields.OLTHAD} }}}}
```

TASK IN QUESTION:
```json
{{{{ {BacktrackerSubAgentInputFields.TASK_IN_QUESTION} }}}}
```

{V1_0_QUESTION}
{WAS_SUCCESSFULLY_COMPLETED_OPTIONS[True].letter}. {WAS_SUCCESSFULLY_COMPLETED_OPTIONS[True].text}
{WAS_SUCCESSFULLY_COMPLETED_OPTIONS[False].letter}. {WAS_SUCCESSFULLY_COMPLETED_OPTIONS[False].text}
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
