from jinja2 import Template

from common.utils import get_prompt_json_spec
from sr_olthad.prompts._strings import (
    EXAMPLE_OLTHAD_FOR_SYS_PROMPT,
    EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT,
)
from sr_olthad.prompts.backtracker._common import (
    BacktrackerSubAgentLmResponseOutputData,
)
from sr_olthad.schema import (
    BinaryChoiceOptions,
    CommonSysPromptInputFields,
    CommonUserPromptInputFields,
    MultipleChoiceQuestionOption,
    PromptRegistry,
    SingleTurnPromptTemplates,
)

EFFORT_WAS_EXHAUSTIVE_OPTIONS: BinaryChoiceOptions = {
    True: MultipleChoiceQuestionOption(
        letter="A",
        text="Yes, all situationally reasonable strategies have been exhausted.",
    ),
    False: MultipleChoiceQuestionOption(
        letter="B",
        text="No, there are still reasonable things that could be done to accomplish the task.",
    ),
}

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
{EXAMPLE_OLTHAD_FOR_SYS_PROMPT}
```

3. Followed by an indication of which in-progress task about which you will be questioned, e.g.:

```text
TASK IN QUESTION:
{EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT}
```

Finally, you will be asked the following:

{V1_0_QUESTION}
{EFFORT_WAS_EXHAUSTIVE_OPTIONS[True].letter}. {EFFORT_WAS_EXHAUSTIVE_OPTIONS[True].text}
{EFFORT_WAS_EXHAUSTIVE_OPTIONS[False].letter}. {EFFORT_WAS_EXHAUSTIVE_OPTIONS[False].text}

You will answer by first carefully thinking things through step-by-step. Only after you've thoroughly reasoned through things, provide a BRIEF final response in a JSON that strictly adheres to the following format:

```json
{get_prompt_json_spec(BacktrackerSubAgentLmResponseOutputData)}
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

TASK IN QUESTION:
```json
{{{{ {CommonUserPromptInputFields.TASK_IN_QUESTION} }}}}
```

{V1_0_QUESTION}
{EFFORT_WAS_EXHAUSTIVE_OPTIONS[True].letter}. {EFFORT_WAS_EXHAUSTIVE_OPTIONS[True].text}
{EFFORT_WAS_EXHAUSTIVE_OPTIONS[False].letter}. {EFFORT_WAS_EXHAUSTIVE_OPTIONS[False].text}
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
