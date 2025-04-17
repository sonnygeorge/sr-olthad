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
        text="It's better to consider the attempt a failure (i.e., semantically, it's more of a one-or-the-other kind of thing).",
    ),
}

######################
######## v1.0 ########
######################


V1_0_QUESTION = "Should the task be considered a partial success?"

SYS_1_0 = f"""You are a helpful thinking assistant that {{{{ {DomainSpecificSysPromptInputFields.LM_ROLE_AS_VERB_PHRASE} }}}}.  Your job is to determine whether a task should be considered a partial success or a failure.

### Your Inputs

You will be provided:

1. A JSON depicting your ongoing progress (memory) and ever-evolving hierarchical plans, where the highest-most (root) task is requested of you by a human user.
PROGRESS/PLANS:
```json
...
```

2. An indication of the "task in question" (i.e., the task you are evaluating the completion of). Please note that the "status" of your "task in question" will be a question mark since you are evaluating it.
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
{WAS_PARTIAL_SUCCESS_OPTIONS[True].letter}. {WAS_PARTIAL_SUCCESS_OPTIONS[True].text}
{WAS_PARTIAL_SUCCESS_OPTIONS[False].letter}. {WAS_PARTIAL_SUCCESS_OPTIONS[False].text}

### Your Response

Carefully think things through step-by-step. Finally, only once you've concluded your deliberation, provide your final response in a JSON that strictly adheres to the following format:

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
