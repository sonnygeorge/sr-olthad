from jinja2 import Template

from enums import BinaryCaseStr
from schema import (
    BinaryChoiceOptions,
    SingleTurnPromptTemplates,
    PromptRegistry,
    MultipleChoiceQuestionAgentOption,
)
from sr_olthad.prompts import SysPromptInsertionField


WAS_PARTIAL_SUCCESS_OPTIONS: BinaryChoiceOptions = {
    BinaryCaseStr.TRUE: MultipleChoiceQuestionAgentOption(
        letter="A",
        text="TODO",  # TODO
    ),
    BinaryCaseStr.FALSE: MultipleChoiceQuestionAgentOption(
        letter="B",
        text="TODO",  # TODO
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


V1_0_QUESTION = "TODO"  # TODO

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

3. Followed by an indication of which in-progress task about which you will be questioned, e.g.:

```text
TASK IN QUESTION:
{{{{ {SysPromptInsertionField.TASK_IN_QUESTION_EXAMPLE} }}}}
```

Finally, you will be asked the following:

{V1_0_QUESTION}
{WAS_PARTIAL_SUCCESS_OPTIONS[BinaryCaseStr.TRUE].letter}. {WAS_PARTIAL_SUCCESS_OPTIONS[BinaryCaseStr.TRUE].text}
{WAS_PARTIAL_SUCCESS_OPTIONS[BinaryCaseStr.FALSE].letter}. {WAS_PARTIAL_SUCCESS_OPTIONS[BinaryCaseStr.FALSE].text}

Think things through step-by-step, considering each of the above points as you go. Finally, provide your final response in a JSON that strictly adheres to the following format:

```json
{{{{ {SysPromptInsertionField.BINARY_OUTPUT_JSON_FORMAT_SPEC} }}}}
```"""

USER_1_0 = f"""CURRENT ACTOR/ENVIRONMENT STATE:
```text
{{{{env_state}}}}
```

PROGRESS/PLANS:
```json
{{{{olthad}}}}
```

TASK IN QUESTION:
```json
{{{{task_in_question}}}}
```

{V1_0_QUESTION}
{WAS_PARTIAL_SUCCESS_OPTIONS[BinaryCaseStr.TRUE].letter}. {WAS_PARTIAL_SUCCESS_OPTIONS[BinaryCaseStr.TRUE].text}
{WAS_PARTIAL_SUCCESS_OPTIONS[BinaryCaseStr.FALSE].letter}. {WAS_PARTIAL_SUCCESS_OPTIONS[BinaryCaseStr.FALSE].text}
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
