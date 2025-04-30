from semantic_steve import SemanticSteve

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

IMPORTANT: If you have postualted a task that is semantically equivalent to a function call, e.g., \"pathfind to coordinates <x,y,z>\", make sure to output it as a function call in your final JSON, e.g., `{"new_planned_subtasks": ["pathfindToCoordinates([12, 12, 12])"]}`. Do all the thinking you need to do before outputting the final JSON.

IMPORTANT: To dig down, just call `pathfindToCoordinates` with a y-coordinate that is lower than your current y-coordinate. DO NOT use `mineBlocks` for this purpose!
"""

ATTEMPT_SUMMARIZER_INSERT = (
    'IMPORTANT: Pay close attention to the "skillInvocationResults" and "inventoryChanges"!'
)

EXAMPLES_TEMPLATE_STR = """
### Examples

Here are some (abbreviated) examples for how to do your job:
{% for example in examples %}
#### Example {{ loop.index }}:

{{ example }}
{% endfor %}
"""
