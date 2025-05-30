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


V1_0_QUESTION = "Can the task in question be considered done? Select the multiple choice label of the statement that is most correct."

SYS_1_0 = f"""You are a helpful thinking assistant that {{{{ {DomainSpecificSysPromptInputFields.LM_ROLE_AS_VERB_PHRASE} }}}}. Your job is to evaluate whether a task has been successfully completed.

## Your Inputs

You will be provided:
1. PROGRESS/PLANS: a JSON depicting your ongoing progress and hierarchical plans, where the root task is your overall goal.
2. TASK IN QUESTION: a JSON object defining the task you are evaluating the completion of. Please note that the `status` of your "task in question" will be a question mark since you are evaluating it.
3. CURRENT ENVIRONMENT STATE: a representation of the most recently observed state of the environment you are in.
4. QUESTION: The question you are to answer.

## Your Response

1. You will assume the most likely interpretation of the "task in question" in the context of the ongoing progress and plans.
2. You will think about what outcome state the "task in question" is phrased to achieve.
3. Considering only how the task is worded. Do **not** extrapolate about hypothetical alternatives to the task in question. Instead, focus on the provided context:
    a. The current environment state
        - Example: Consider the quantitative evidence of the environment state. E.g., if you want 4 'strawberries', and you currently have 2 'strawberries', that is not enough to consider the task completed.
    b. Previous retrospectives and tasks.
        - Example: If you want 4 'strawberries' and you currently have 8, there may be a reason why you still want 4 'more'. If so, it will be inferrable by reflecting over the previous retrospectives and task trajectory.
4. You will reason about any found evidence (or lack thereof).
5. Only after completing steps 1-5, you will output your final answer as a JSON that strictly adheres to this specification:

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
{WAS_SUCCESSFULLY_COMPLETED_OPTIONS[True].letter}. {WAS_SUCCESSFULLY_COMPLETED_OPTIONS[True].text}
{WAS_SUCCESSFULLY_COMPLETED_OPTIONS[False].letter}. {WAS_SUCCESSFULLY_COMPLETED_OPTIONS[False].text}

Remember to follow your 5-step instructions for your response.

IMPORTANT: Retrospectives should be short: 1-4 sentences of the important takeaways.

IMPORTANT: Completion of a task should be kept in context to that task only. Completion of higher-level tasks is not decided with the completion of a subtask.

IMPORTANT: Having the "ability" to complete the current task, given the current environment state, is NOT completing the current task.
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
