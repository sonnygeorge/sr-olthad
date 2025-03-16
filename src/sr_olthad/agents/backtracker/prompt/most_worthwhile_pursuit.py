from jinja2 import Template

from sr_olthad.agents.backtracker.prompt.common import (
    JSON_FORMAT_SYS_PROMPT_INSERT,
    BacktrackerSubAgentInputFields,
)
from sr_olthad.agents.prompt import (
    EXAMPLE_OLTHAD_FOR_SYS_PROMPT,
    EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT,
)
from sr_olthad.schema import (
    MultipleChoiceQuestionOption,
    PromptRegistry,
    SingleTurnPromptTemplates,
)
from sr_olthad.utils import BinaryChoiceOptions

IS_MOST_WORTHWHILE_OPTIONS: BinaryChoiceOptions = {
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
{IS_MOST_WORTHWHILE_OPTIONS[True].letter}. {IS_MOST_WORTHWHILE_OPTIONS[True].text}
{IS_MOST_WORTHWHILE_OPTIONS[False].letter}. {IS_MOST_WORTHWHILE_OPTIONS[False].text}

Now, there are many possible reasons why answer choice "B" might be better. Here are a few examples:
1. The task was foolishly proposed/poorly conceived in the first place (e.g., was not the best idea or was ambiguously phrased).
2. There is some—now more useful—thing that falls outside of the semantic scope of how the task is phrased—regardless of whether, by virtue of some now-evident reason:
    1. **Only a _slight_ semantic tweak to the task is warranted**
        - E.g., let's say the task in question was to 'pick strawberries' in order to 'get some fruit.' If it has become evident that the nearest available fruit bush is raspberry, adjusting 'pick strawberries' to 'pick raspberries' may now be more appropriate.
    2. Or, **a semantically different task should replace it (at least for now)**.
        - E.g., the task, although perhaps still useful as-is, should be shelved in favor of something else
        - E.g., the utility of the task has been rendered moot altogether (e.g., if the task was to 'find a TV show to help Lisa fall asleep' and it was clear that Lisa had already fallen asleep).
3. Something has emerged that makes the task significantly harder than perhaps was previously assumed, making it less worthwhile in light of potentially easier alternatives.
4. ...

Think things through step-by-step, considering each of the above points as you go. Finally, only once you've concluded your deliberation, provide your final response in a JSON that strictly adheres to the following format:

```json
{JSON_FORMAT_SYS_PROMPT_INSERT}
```

IMPORTANT: The highest-level task with id "1" is the highly important user-requested task. If this task is in question, you should only answer {IS_MOST_WORTHWHILE_OPTIONS[False].letter} IF THE TASK IS IMMORAL OR LEARNED TO BE IMPOSSIBLE. DO NOT ABANDON THE HIGHEST-LEVEL IN FAVOR OF SOMETHING ELSE!
"""

USER_1_0 = f"""CURRENT ACTOR/ENVIRONMENT STATE:
```text
{{{{ {BacktrackerSubAgentInputFields.ENV_STATE} }}}}
```

PROGRESS/PLANS:
```json
{{{{ {BacktrackerSubAgentInputFields.OLTHAD} }}}}
```

TASK IN QUESTION:
```json
{{{{ {BacktrackerSubAgentInputFields.TASK_IN_QUESTION} }}}}
```

{V1_0_QUESTION}
{IS_MOST_WORTHWHILE_OPTIONS[True].letter}. {IS_MOST_WORTHWHILE_OPTIONS[True].text}
{IS_MOST_WORTHWHILE_OPTIONS[False].letter}. {IS_MOST_WORTHWHILE_OPTIONS[False].text}
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
