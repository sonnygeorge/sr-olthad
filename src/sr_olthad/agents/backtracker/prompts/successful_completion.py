from jinja2 import Template

from enums import BinaryCaseStr
from schema import (
    BinaryChoiceOptions,
    SingleTurnPromptTemplates,
    PromptRegistry,
    MultipleChoiceQuestionAgentOption,
)
from sr_olthad.enums import AttemptedTaskStatus
from sr_olthad.prompts import SysPromptInsertionField


WAS_SUCCESSFULLY_COMPLETED_OPTIONS: BinaryChoiceOptions = {
    BinaryCaseStr.TRUE: MultipleChoiceQuestionAgentOption(
        letter="A",
        text="It can be said with confidence that the task has now been successfully completed.",
    ),
    BinaryCaseStr.FALSE: MultipleChoiceQuestionAgentOption(
        letter="B",
        text="What the task is aiming to achieve has not yet been fully realized.",
    ),
}

SYS_PROMPT_INSERTION_FIELDS_NEEDED = [
    SysPromptInsertionField.OLTHAD_EXAMPLE,
    SysPromptInsertionField.TASK_IN_QUESTION_EXAMPLE,
    SysPromptInsertionField.BINARY_OUTPUT_JSON_FORMAT_SPEC,
]


######################
######## v1.0 ########
######################


V1_0_QUESTION = "Given this up-to-date state of everything, can the task in question be considered done? I.e., which statement is more true?"

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
{{{{ {SysPromptInsertionField.OLTHAD_EXAMPLE} }}}}
```

3. Followed by an indication of which in-progress task to which you will consider assigning the "{AttemptedTaskStatus.SUCCESS}" status. E.g.,:

```text
TASK WHOSE STATUS IS IN QUESTION:
{{{{ {SysPromptInsertionField.TASK_IN_QUESTION_EXAMPLE} }}}}
```

Finally, you will be asked the following:

{V1_0_QUESTION}
{WAS_SUCCESSFULLY_COMPLETED_OPTIONS[BinaryCaseStr.TRUE].letter}. {WAS_SUCCESSFULLY_COMPLETED_OPTIONS[BinaryCaseStr.TRUE].text}
{WAS_SUCCESSFULLY_COMPLETED_OPTIONS[BinaryCaseStr.FALSE].letter}. {WAS_SUCCESSFULLY_COMPLETED_OPTIONS[BinaryCaseStr.FALSE].text}

You will answer by first carefully thinking things through step-by-step. Only after you've thoroughly reasoned through things, provide your final response in a JSON that strictly adheres to the following format:

```json
{{{{ {SysPromptInsertionField.BINARY_OUTPUT_JSON_FORMAT_SPEC} }}}}
```"""

USER_1_0 = f"""CURRENT ACTOR/ENVIRONMENT STATE:
{{{{env_state}}}}

PROGRESS/PLANS:
{{{{olthad}}}}

TASK WHOSE STATUS IS IN QUESTION:
{{{{task_in_question}}}}

{V1_0_QUESTION}
{WAS_SUCCESSFULLY_COMPLETED_OPTIONS[BinaryCaseStr.TRUE].letter}. {WAS_SUCCESSFULLY_COMPLETED_OPTIONS[BinaryCaseStr.TRUE].text}
{WAS_SUCCESSFULLY_COMPLETED_OPTIONS[BinaryCaseStr.FALSE].letter}. {WAS_SUCCESSFULLY_COMPLETED_OPTIONS[BinaryCaseStr.FALSE].text}
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
