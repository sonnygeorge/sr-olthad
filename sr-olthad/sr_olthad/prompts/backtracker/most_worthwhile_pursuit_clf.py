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

IS_MOST_WORTHWHILE_PURSUIT_OPTIONS: BinaryChoiceOptions = {
    True: MultipleChoiceQuestionOption(
        letter="A",
        text="The task in question is, at this time, the most worthwhile objective for the actor to be pursuing.",
    ),
    False: MultipleChoiceQuestionOption(
        letter="B",
        text="The task in question should be dropped, at least temporarily, in favor of something else.",
    ),
}

######################
######## v1.0 ########
######################


V1_0_QUESTION = "Which statement is more true?"

SYS_1_0 = f"""You are a helpful thinking assistant that {{{{ {DomainSpecificSysPromptInputFields.LM_ROLE_AS_VERB_PHRASE} }}}}. Your job is determine whether a task is still your most worthy pursuit.

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
{IS_MOST_WORTHWHILE_PURSUIT_OPTIONS[True].letter}. {IS_MOST_WORTHWHILE_PURSUIT_OPTIONS[True].text}
{IS_MOST_WORTHWHILE_PURSUIT_OPTIONS[False].letter}. {IS_MOST_WORTHWHILE_PURSUIT_OPTIONS[False].text}

### Food For Thought

Now, there are many possible reasons why answer choice "B" might be better. Here are a few examples:
1. The "task in question" was foolishly proposed/poorly conceived in the first place (e.g., was not the best idea or was ambiguously phrased).
2. There is some—now more useful—thing that falls outside of the semantic scope of how the "task in question" is phrased... regardless of whether, by virtue of some now-evident reason:
    1. **Only a _slight_ semantic tweak to the "task in question" is warranted**
        - E.g., let's say the "task in question" was to 'pick strawberries' in order to 'get some fruit.' If it has become evident that the nearest available fruit bush is raspberry, adjusting 'pick strawberries' to 'pick raspberries' may now be more appropriate.
    2. Or, **a semantically different task should replace the "task in question" (at least for now)**.
        - E.g., the "task in question", although perhaps still useful as-is, should be shelved in favor of something else
        - E.g., the utility of the "task in question" has been rendered moot altogether (e.g., if the "task in question" was to 'find a lullaby to help Lisa fall asleep' and it was clear that Lisa had already fallen asleep).
3. Something has emerged that makes the "task in question" significantly harder than perhaps was previously assumed, making it less worthwhile in light of potentially easier alternatives.
4. ...

IMPORTANT: The highest-level task with id "1" is was requested of you by a human user. Therefore, if it is the "task in question", you should never favor pursuing something else (such an opinion would not override the user's). The root task with id "1" is inherently more worthwhile than alternatives BECAUSE THE USER REQUESTED IT! Nevertheless, you should propose dropping the root task if it is immoral or learned to be impossible, otherwise answer {IS_MOST_WORTHWHILE_PURSUIT_OPTIONS[True].letter} if the user-requested root task with id "1" is the "task in question".

### Your Response

YOU MUST FOLLOW THESE INSTRUCTIONS:

Instructions:
1. If the task in question is the highest-level task (id "1") and it is _not_ immoral (according to your judgment) or _truly_ impossible (e.g., because of some discovered thing), answer {IS_MOST_WORTHWHILE_PURSUIT_OPTIONS[True].letter}. This is because if the user requested the task, it is always inherently more worthwhile than alternatives. If this user-requested root task is immoral or impossible, answer {IS_MOST_WORTHWHILE_PURSUIT_OPTIONS[False].letter} and explain why in you final response JSON.
2. If the task in question is not the highest-level task (id "1"). Think things through step-by-step, considering each of the points in ['Food For Thought'](#food-for-thought). Finally, only once you've concluded your deliberation, provide your final response JSON.

In all cases, you will conclude by outputting your final response JSON that strictly adheres to the following format:
```json
{get_prompt_json_spec(BacktrackerSubAgentLmResponseOutputData)}
```

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
{IS_MOST_WORTHWHILE_PURSUIT_OPTIONS[True].letter}. {IS_MOST_WORTHWHILE_PURSUIT_OPTIONS[True].text}
{IS_MOST_WORTHWHILE_PURSUIT_OPTIONS[False].letter}. {IS_MOST_WORTHWHILE_PURSUIT_OPTIONS[False].text}

Remember to follow your instructions by first checking if the task in question is the root task (id "1") and adapting your evaluation accordingly.
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
