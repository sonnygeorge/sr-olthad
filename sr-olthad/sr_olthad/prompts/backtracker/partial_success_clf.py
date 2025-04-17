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

WAS_PARTIAL_SUCCESS_OPTIONS: BinaryChoiceOptions = {
    True: MultipleChoiceQuestionOption(
        letter="A",
        text="It's better to think about the stated outcome(s) as having been partially realized.",
    ),
    False: MultipleChoiceQuestionOption(
        letter="B",
        text="It's better to consider the attempt a failure.",
    ),
}

######################
######## v1.0 ########
######################


V1_0_QUESTION = "Should the task be considered a partial success?"

SYS_1_0 = f"""You are a helpful thinking assistant that {{{{ {DomainSpecificSysPromptInputFields.LM_ROLE_AS_VERB_PHRASE} }}}}.  Your job is to determine whether a task should be considered a partial success or a failure.

### Your Inputs

You will be provided:

1. PROGRESS/PLANS: a JSON depicting your ongoing progress and hierarchical plans, where the root task is your overall goal.
2. TASK IN QUESTION: a JSON object defining the task you are evaluating the completion of. Please note that the `status` of your "task in question" will be a question mark since you are evaluating it.
3. CURRENT ENVIRONMENT STATE: a representation of the most recently observed state of the environment you are in.
4. QUESTION: The question you are to answer.

### Your Response

Carefully think things through step-by-step. Finally, once you've concluded your thinking, provide your final response in a JSON that strictly adheres to the following format:

```json
{get_prompt_json_spec(BacktrackerSubAgentLmResponseOutputData)}
```

### Auxiliary Information About Domain

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
{WAS_PARTIAL_SUCCESS_OPTIONS[True].letter}. {WAS_PARTIAL_SUCCESS_OPTIONS[True].text}
{WAS_PARTIAL_SUCCESS_OPTIONS[False].letter}. {WAS_PARTIAL_SUCCESS_OPTIONS[False].text}

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
