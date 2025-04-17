from typing import ClassVar

from jinja2 import Template
from pydantic import BaseModel, Field

from sr_olthad.framework.utils import get_prompt_json_spec
from sr_olthad.prompts._strings import (
    EXAMPLE_OLTHAD_FOR_SYS_PROMPT,
    EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT,
)
from sr_olthad.schema import (
    DomainSpecificSysPromptInputFields,
    PromptRegistry,
    SingleTurnPromptTemplates,
    UserPromptInputFields,
)


class PlannerLmResponseOutputData(BaseModel):
    """
    Data to be parsed from the LM's response within the Planner.

    Attributes:
        new_planned_subtasks (list[str]): The new set of planned subtasks for the node
            in question.
    """

    # NOTE: These must correspond to the field attrs below.
    new_planned_subtasks_attr: ClassVar[str] = "new_planned_subtasks"

    # Fields
    new_planned_subtasks: list[str] = Field(
        description="The new set of planned subtasks for the node in question.",
        json_schema_extra={"field_type": "list[str]"},
    )


######################
######## v1.0 ########
######################

SYS_1_0 = f"""You are a helpful thinking assistant that {{{{ {DomainSpecificSysPromptInputFields.LM_ROLE_AS_VERB_PHRASE} }}}}. Your specific job is to create and update tentative plans at a conservative next-most level of granularity.

### Your Inputs

You will be provided:

1. A representation of the most recently observed state of the world (i.e., the environment you are in).
CURRENT ENVIRONMENT STATE:
...

2. A JSON depicting your ongoing progress (memory) and ever-evolving hierarchical plans, where the highest-most (root) task is requested of you by a human user. E.g.:
PROGRESS/PLANS:
```json
{EXAMPLE_OLTHAD_FOR_SYS_PROMPT}
```

3. An indication of the "task in question" (i.e., the task for which you will be determining appropriate planned subtasks). E.g.:
```text
TASK IN QUESTION:
{EXAMPLE_TASK_IN_QUESTION_FOR_SYS_PROMPT}
```


IMPORTANT: For determining your response, pay close attention to following the domain-specific information so that your outputs adhere to the system and best practices of the domain!

### Crucial Information About Domain

{{{{ {DomainSpecificSysPromptInputFields.DOMAIN_EXPOSITION} }}}}


### Your Response

Regardless of whether the task in question has tentatively planned subtasks, your job is to consider how things are progressing (with respect to the aims/plans towards parent outcomes) and provide an updated set of tentatively planned subtasks for the task in question. This, your updated set will replace any existing tentatively planned subtasks. Therefore, e.g., if the existing tentatively planned subtasks are fine as-is, simply list them back and they will be fed back into system with no change.

Since the system is designed to gradually break down tasks as much as needed, you should not over-granularize the planned subtasks too early. Instead focus on planning at a sensible next-most level of abstraction that will help define crucial task-concepts without planning forward too much detail. After all, the future is often uncertain and it would be inefficient to speculate too granularly far into the future. When planning at high levels of abstraction, focus on crucial strategic steps that will roughly outline good strategies. Then, when planning at lower levels of abstraction, you'll have enough strategical context to inform more detailed steps. Focus intently on conforming your plans to be intelligent given what you are observing in the environment. Think about past retrospectives and try not to fall into the same repetitive patterns or repeat futile actions/strategies.

Rules for subtasks:
1. If the current "task in question" is a "skill" function call, LEAVE IT. you are done, this is the most that we can subdivide it. This is an atomic operation.
2. Sub-tasks should not incorporate the same broad goal as its parent task. A sub task should be a more granularized, specific section of the parent task. There should definitely be zero repeats.
3. Interacting with the environment can ONLY happen through the above "skills". If your subtasks involve interacting with the environment, you must use a skill to do so. If you are attempting to interact with the environment and it appears that there is no skill to do so, this is an INVALID subtask and MUST not be considered.
4. There may be multiple solutions to a given problem. Prioritize subtasks that utilize information known from the current environment over solutions that require exploration.
5. When creating subtasks, remember to look up at the parent task's ancestors to see if you are repeating logic. If you are, do not include those repeated subtasks.
6. subtasks that cover a broad scope should not use suggestive language.
    - Example: If you need to get ingredients for a cake, you should not say "Buy ingredients", but "Acquire ingredients". 
        - Reasoning: You may have ingredients at home, but you would not "plan" for that if you suggest "buying" ingredients.


Carefully think step-by-step. Finally, only once you've concluded your deliberation, provide your final response in list that strictly adheres to the following format:

current task: <task>
<explanation about why these subtasks, one bullet point per each>

subtasks: [...] (string list)

Now, before we show this response, we need to consider the following:
Look at the "task in question". Then, compare each subtask to it. If they are essentially the same task, just reworded, remove the subtask entirely from the list.

Tell the user this comparison for every subtask. put it at the end of your output.

If there are no more subtasks remaining, you need to reconsider the task again, focusing on granularizing it down to more specific tasks.


The final, final output of the fully completed list of subtasks should be a JSON string that strictly adheres to the following format:
```json
{get_prompt_json_spec(PlannerLmResponseOutputData)}
```


"""

USER_1_0 = f"""CURRENT ENVIRONMENT STATE:
{{{{ {UserPromptInputFields.ENV_STATE} }}}}

PROGRESS/PLANS:
```json
{{{{ {UserPromptInputFields.OLTHAD} }}}}
```

TASK IN QUESTION:
```json
{{{{ {UserPromptInputFields.TASK_IN_QUESTION} }}}}
```

IMPORTANT: Top level tasks, that cover a broad scope, should not use suggestive language.
    - Example: If you need to get ingredients for a cake, you should not say "Buy ingredients", but "Acquire ingredients". 
        - Reasoning: You may have ingredients at home, but you would not "plan" for that if you suggest "buying" ingredients.

IMPORTANT: Planned subtasks MUST be phrased in imperative tense, e.g. "Do X".

IMPORTANT: Do not phrase subtasks with any conditionals, e.g. "If X, then do Y", "do Y if X".
    - Example: "If I have 5 apples, then do X" should be "Do X with 5 apples".
        - Reasoning: 
            - You are not trying to reason about the future, you are trying to plan for it.
            - If you need to do something if a condition is met, you should just plan for that condition to be met.
 
IMPORTANT: Do not repeat previous tasks unnecessarily!
    - Example: "Do X with 5 apples" task leading to "With 5 apples do X"
    - Example: If your task was "get 5 apples", ALL of your subtasks CANNOT include "get 5 apples", or any close derivative of the original task.
        - Fix: "get 5 apples" task needs new_planned_subtasks like: ["move to the store", "buy 5 apples"]
        
IMPORTANT: Logical precursors to our current state may have already occurred. Reflect on the environment state and determine whether you have completed the prerequesites for the current task.
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
