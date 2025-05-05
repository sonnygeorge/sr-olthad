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


V1_0_QUESTION = "Thinking ONLY about what's been done so far, has the task been given an exhaustive effort or are there still obvious things could be done to accomplish it? Which of the following statements is more true?"

SYS_1_0 = f"""You are a helpful thinking assistant that {{{{ {DomainSpecificSysPromptInputFields.LM_ROLE_AS_VERB_PHRASE} }}}}. Your specific job is to decide whether a task has been given a reasonably exhaustive effort given your situation.

## Your Inputs

You will be provided:

1. PROGRESS/PLANS: a JSON depicting your ongoing progress and hierarchical plans, where the root task is your overall goal.
2. TASK IN QUESTION: a JSON object defining the task you are evaluating the completion of. Please note that the `status` of your "task in question" will be a question mark since you are evaluating it.
3. CURRENT ENVIRONMENT STATE: a representation of the most recently observed state of the environment you are in.
4. QUESTION: The question you are to answer.

## Your Response

1. You will think step-by-step about (1) what, in your current situation, a "reasonably exhaustive effort" might entail, and (2) whether the attempted effort (attempted subtasks of the "TASK IN QUESTION", if any) has been exhaustive:
    - Given a realistic evaluation of your capabilities, have you exhausted all situationally *reasonable* strategies for accomplishing this task?
    - Are you leaving obvious steps/strategies on the table? (Think about what you have available to you in your environment and what, given this, you might be capable of.)
2. After reasoning through the above, you will output your final answer as a JSON that strictly adheres to this specification:

```json
{get_prompt_json_spec(BacktrackerSubAgentLmResponseOutputData)}
```

## Auxiliary Information About Domain

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

IMPORTANT: Retrospectives should be short: 1-2 sentences of the important takeaways.
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
