from jinja2 import Template

from enums import BinaryCaseStr
from schema import (
    BinaryChoiceOptions,
    SingleTurnPromptTemplates,
    PromptRegistry,
    MultipleChoiceQuestionAgentOption,
)
from sr_olthad.prompts import SysPromptInsertionField


IS_MOST_WORTHWHILE_OPTIONS: BinaryChoiceOptions = {
    BinaryCaseStr.TRUE: MultipleChoiceQuestionAgentOption(
        letter="A",
        text="The task in question is, at this time, the most worthwhile objective for the actor to be pursuing.",
    ),
    BinaryCaseStr.FALSE: MultipleChoiceQuestionAgentOption(
        letter="B",
        text="The task in question should be dropped, at least temporarily, in favor of something else.",
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


V1_0_QUESTION = "Given the current state of everything, which statement is more true?"

SYS_1_0 = f"""You are a helpful AI assistant who plays a crucial role in a decision-making system designed to help an actor achieve any-horizon goals through hierarchical temporal reasoning. Your specific job is as follows.

You will be given:

1. Information representing the current state of the actor and environment:

```text
CURRENT ACTOR/ENVIRONMENT STATE:
...
```

2. Followed by a hierarchical representation of the actor's progress and future plans towards a highest-level goal, e.g.:

```text
PROGRESS/PLANS:
{{{{ {SysPromptInsertionField.OLTHAD_EXAMPLE} }}}}
```

3. Followed by an indication of which in-progress task is the task you will be considering, e.g.,:

```text
TASK IN QUESTION:
{{{{ {SysPromptInsertionField.TASK_IN_QUESTION_EXAMPLE} }}}}
```

Finally, you will be asked the following:

{V1_0_QUESTION}
{IS_MOST_WORTHWHILE_OPTIONS[BinaryCaseStr.TRUE].letter}. {IS_MOST_WORTHWHILE_OPTIONS[BinaryCaseStr.TRUE].text}
{IS_MOST_WORTHWHILE_OPTIONS[BinaryCaseStr.FALSE].letter}. {IS_MOST_WORTHWHILE_OPTIONS[BinaryCaseStr.FALSE].text}

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

Think things through step-by-step, considering each of the above points as you go. Finally, provide your final response in a JSON that strictly adheres to the following format:

```json
{{{{ {SysPromptInsertionField.BINARY_OUTPUT_JSON_FORMAT_SPEC} }}}}
```"""

USER_1_0 = f"""CURRENT ACTOR/ENVIRONMENT STATE:
{{{{env_state}}}}

PROGRESS/PLANS:
{{{{olthad}}}}

TASK IN QUESTION:
{{{{task_in_question}}}}

{V1_0_QUESTION}
{IS_MOST_WORTHWHILE_OPTIONS[BinaryCaseStr.TRUE].letter}. {IS_MOST_WORTHWHILE_OPTIONS[BinaryCaseStr.TRUE].text}
{IS_MOST_WORTHWHILE_OPTIONS[BinaryCaseStr.FALSE].letter}. {IS_MOST_WORTHWHILE_OPTIONS[BinaryCaseStr.FALSE].text}
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
