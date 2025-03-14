from jinja2 import Template

from enums import BinaryCaseStr
from schema import (
    BinaryChoiceOptions,
    SingleTurnPromptTemplates,
    PromptRegistry,
    MultipleChoiceQuestionAgentOption,
)
from sr_olthad.prompts import SysPromptInsertionField


EFFORT_WAS_EXHAUSTIVE_OPTIONS: BinaryChoiceOptions = {
    BinaryCaseStr.TRUE: MultipleChoiceQuestionAgentOption(
        letter="A",
        text="Yes, all situationally reasonable strategies have been exhausted.",
    ),
    BinaryCaseStr.FALSE: MultipleChoiceQuestionAgentOption(
        letter="B",
        text="No, there are still reasonable things that could be done to accomplish the task.",
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


V1_0_QUESTION = "Thinking ONLY about what's been done so far, has the task been given an exhaustive effort or, are there still obvious things we could do to accomplish it? Which of the following statements is more true?"

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
{EFFORT_WAS_EXHAUSTIVE_OPTIONS[BinaryCaseStr.TRUE].letter}. {EFFORT_WAS_EXHAUSTIVE_OPTIONS[BinaryCaseStr.TRUE].text}
{EFFORT_WAS_EXHAUSTIVE_OPTIONS[BinaryCaseStr.FALSE].letter}. {EFFORT_WAS_EXHAUSTIVE_OPTIONS[BinaryCaseStr.FALSE].text}

You will answer by first carefully thinking things through step-by-step. Only after you've thoroughly reasoned through things, provide a BRIEF final response in a JSON that strictly adheres to the following format:

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
{EFFORT_WAS_EXHAUSTIVE_OPTIONS[BinaryCaseStr.TRUE].letter}. {EFFORT_WAS_EXHAUSTIVE_OPTIONS[BinaryCaseStr.TRUE].text}
{EFFORT_WAS_EXHAUSTIVE_OPTIONS[BinaryCaseStr.FALSE].letter}. {EFFORT_WAS_EXHAUSTIVE_OPTIONS[BinaryCaseStr.FALSE].text}
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
