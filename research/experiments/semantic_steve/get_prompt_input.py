from jinja2 import Template
from semantic_steve import SemanticSteve

from research.experiments.semantic_steve.rag.retrieve import retrieve
from sr_olthad import (
    DomainSpecificSysPromptInputData,
    LmAgentName,
    UserPromptInputData,
)

LM_ROLE_AS_VERB_PHRASE = SemanticSteve.get_user_role_as_verb_phrase()
SKILLS_DOCS_STR = "\n\n".join(SemanticSteve.get_skills_docs())
SKILLS_DOCS_INSERT = f"\n### Skill Functions Available\n\nHere is the documentation for what skill functions are available to you:\n{SKILLS_DOCS_STR}\n"
DOMAIN_EXPOSITION_TEMPLATE = """You are controlling a Minecraft player using SemanticSteve, a library that wraps playing the game of Minecraft with textual world-state observations and idiomatic "skill"-function calling. You are playing VANILLA survival minecraft in peaceful mode. All normal game mechanics, concepts, recipes, etc. apply. There are no mods or plugins. DO NOT hallucinate game mechanics.
{{ skills_docs }}
"""

PLANNER_INSERT = """IMPORTANT: When a subtask aligns with an available function, you must output tasks that are syntactically-valid function calls to the SemanticSteve skill functions.

For example, if the "task in question" was "gather wood" and an "oak_log" was visible in your immediate surroundings, you should probably plan at least one task that is a syntactically-valid invocation of the `mineBlocks` function, e.g., you could output something like `["mineBlocks('oak_log')"]`.

This logic also applies to other skills, such as `craftItems`, `placeBlocks`, and `useItems`. For example, if the "task in question" was "craft 1 furnace from 8 cobblestone" and you had 8 'cobblestone' in your inventory, you could output something like `["craftItems('furnance', 1)"]` due to the skill handling the finer logic.

Remember, however, that you are to break down tasks into further high-level subtasks in open-ended natural language until you reach a situation where it is appropriate to output a skill-function call. E.g., if the "task in question" was to "gather wood", but there were no logs or planks in your surroundings, you should break down the task further until you are certain that a function-call is appropriate, e.g., `["explore to find some form of planks or logs", "gather the planks or logs"]`.

Pay attention to the documentation for how to use the functions to make sure you are invoking them correctly in appropriate situations (i.e., when they are likely to succeed). Do not hallucinate functions that are not available to you. Only use the functions that are documented above.

IMPORTANT: If you are interacting with items, make sure to specifically articulate the quantities of items involved in tasks.
    - Example: "Obtain more oak planks" should be, e.g., "Obtain X more oak planks on top of the Y we already have to raise our total to Z".

IMPORTANT: You define a task as "granular enough" to be a valid skill function call if the task is a single, atomic action that can be performed in the game world. This means that the task should be specific enough to be accomplished with a single function call, without requiring any additional context or information. For example, "mine a block", "craft 3 X's from Y", "place W at x,y,z", "place W", would be considered granular enough to be a valid skill function call, while "gather resources" or "build a house" would not be granular enough.

IMPORTANT: If the context IS granularly scoped such that a next-most planned subtask could be a function call, it is IMPERATIVE that you plan a task that is a function call, e.g., if the task was 'get planks' and you had 6 `oak_logs` in your inventory:\n```json\n{\n"new_planned_subtasks": ["craftItems('oak_planks', 24)"]\n}```.

IMPORTANT: If you have postulated a task that is semantically equivalent to a function call, e.g., \"pathfind to coordinates <x,y,z>\", make sure to output it as a function call in your final JSON, e.g., `{"new_planned_subtasks": ["pathfindToCoordinates([12, 12, 12])"]}`. Do all the thinking you need to do before outputting the final JSON.

IMPORTANT: To dig down, just call `pathfindToCoordinates` with a y-coordinate that is lower than your current y-coordinate. DO NOT use `mineBlocks` for this purpose!

IMPORTANT: The best way to explore is to approach things in the distant surroundings that you think might lead you to your goal. Make sure not to backtrack! Every now and then, use pathfindToCoordinates to move you to a new location entirely.
"""

ATTEMPT_SUMMARIZER_INSERT = (
    'IMPORTANT: Pay close attention to the "skillInvocationResults" and "inventoryChanges"!'
)

SUCCESSFUL_COMPLETION_CLF_INSERT = "IMPORTANT: Under no circumstances should you ever consider a task that involves taking a screenshot to be complete without a screenshot being taken! Even if all of the setup for the screenshot has occured, there must be evidence that a screenshot has been taken!!!\n"

EXHAUSTIVE_EFFORT_CLF_INSERT = "IMPORTANT: Under no circumstances should you ever consider a task that involves taking a screenshot to have been given an exhaustive effort if no attempt to take a screenshot has been made! Unless all courses of action for setting up the screenshot have been exhausted to no avail, you must NEVER say that a screenshot task has been given an exhaustive effort without a screenshot actually being taken/attempted!!! NEVER, EVER DO THIS!!!\n"


EXAMPLES_TEMPLATE_STR = """
### Examples

Here are some (abbreviated) examples for how to do your job:
{% for example in examples %}
#### Example {{ loop.index }}:

{{ example }}
{% endfor %}
"""


AGENTS_FOR_WHICH_TO_SHOW_EXAMPLES = [LmAgentName.PLANNER]
AGENTS_FOR_WHICH_TO_SHOW_SKILLS_DOCS = [LmAgentName.PLANNER, LmAgentName.ATTEMPT_SUMMARIZER]


def get_semantic_steve_sys_prompt_input_data(
    lm_agent_name: LmAgentName,
    user_prompt_input_data: UserPromptInputData,
    n_few_shot_examples: int = 0,
) -> DomainSpecificSysPromptInputData:
    # TODO: (Dynamically?) render in (situation-relevent) tips?

    main_template: Template = Template(DOMAIN_EXPOSITION_TEMPLATE)

    # Insert skills docs if applicable
    if lm_agent_name in AGENTS_FOR_WHICH_TO_SHOW_SKILLS_DOCS:
        domain_exposition = main_template.render(skills_docs=SKILLS_DOCS_INSERT)
    else:
        domain_exposition = main_template.render(skills_docs="")

    # Insert specialized inserts
    if lm_agent_name == LmAgentName.PLANNER:
        domain_exposition += "\n\n" + PLANNER_INSERT
    elif lm_agent_name == LmAgentName.ATTEMPT_SUMMARIZER:
        domain_exposition += "\n\n" + ATTEMPT_SUMMARIZER_INSERT
    elif lm_agent_name == LmAgentName.SUCCESSFUL_COMPLETION_CLF:
        domain_exposition += "\n\n" + SUCCESSFUL_COMPLETION_CLF_INSERT
    elif lm_agent_name == LmAgentName.EXHAUSTIVE_EFFORT_CLF:
        domain_exposition += "\n\n" + EXHAUSTIVE_EFFORT_CLF_INSERT

    # Insert few shot examples if applicable
    if n_few_shot_examples > 0 and lm_agent_name in AGENTS_FOR_WHICH_TO_SHOW_EXAMPLES:
        examples_template: Template = Template(EXAMPLES_TEMPLATE_STR)
        if n_few_shot_examples > 0:
            examples = retrieve(n_few_shot_examples, user_prompt_input_data, lm_agent_name)
            examples_str = examples_template.render(examples=examples)
            domain_exposition += "\n\n" + examples_str

    return DomainSpecificSysPromptInputData(
        lm_role_as_verb_phrase=LM_ROLE_AS_VERB_PHRASE,
        domain_exposition=domain_exposition,
    )
