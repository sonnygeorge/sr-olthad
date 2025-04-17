from jinja2 import Template

from sr_olthad.framework.utils import get_prompt_json_spec
from sr_olthad.prompts.backtracker._common import (
    BacktrackerSubAgentLmResponseOutputData,
)
from sr_olthad.schema import (
    BinaryChoiceOptions,
    DomainSpecificSysPromptInputFields,
    MultipleChoiceQuestionOption,
    PromptRegistry,
    SingleTurnPromptTemplates,
    UserPromptInputFields,
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

SYS_1_0 = f"""You are a helpful thinking assistant that {{{{ {DomainSpecificSysPromptInputFields.LM_ROLE_AS_VERB_PHRASE} }}}}. Your specific job is to decide whether a task has been given a reasonably exhaustive effort given your situation.

### Your Inputs

You will be provided:

1. A JSON depicting your ongoing progress (memory) and ever-evolving hierarchical plans, where the highest-most (root) task is requested of you by a human user.
PROGRESS/PLANS:
```json
...
```

2. An indication of the "task in question" (i.e., the task you are evaluating the effort of). Please note that the "status" of your "task in question" will be a question mark since you are evaluating it.
TASK IN QUESTION:
```json
...
```

3. A representation of the most recently observed state of the world (i.e., the environment you are in).
CURRENT ENVIRONMENT STATE:
...

4. The question you are being asked:
QUESTION:
{V1_0_QUESTION}
{EFFORT_WAS_EXHAUSTIVE_OPTIONS[True].letter}. {EFFORT_WAS_EXHAUSTIVE_OPTIONS[True].text}
{EFFORT_WAS_EXHAUSTIVE_OPTIONS[False].letter}. {EFFORT_WAS_EXHAUSTIVE_OPTIONS[False].text}

### Your Response

1. You will reason about (1) what, in your current situation, a "reasonably exhaustive effort" might entail, and (2) whether the attempted effort (attempted subtasks of the "task in question", if any) has been exhaustive:
    - Given a realistic evaluation of your capabilities, have you exhausted all situationally reasonable strategies for accomplishing this task? (You don't need to "go to the ends of the earth"; just try all the reasonable approaches.)
    - Are you leaving obvious steps/strategies on the table? (Think about what you have available to you in your environment and what, given this, you might be capable of.)
2. Only after reasoning through the above, you will output your final answer as a JSON that strictly adheres to this specification:

```json
{get_prompt_json_spec(BacktrackerSubAgentLmResponseOutputData)}
```

### Potentially Useful Auxiliary Information About Domain

{{{{ {DomainSpecificSysPromptInputFields.DOMAIN_EXPOSITION} }}}}"""

USER_1_0 = f"""PROGRESS/PLANS:
```json
{{{{ {UserPromptInputFields.OLTHAD} }}}}
```

TASK IN QUESTION:
```json
{{{{ {UserPromptInputFields.TASK_IN_QUESTION} }}}}
```

CURRENT ENVIRONMENT STATE:
{{{{ {UserPromptInputFields.ENV_STATE} }}}}

QUESTION:
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
