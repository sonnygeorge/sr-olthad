from jinja2 import Template
from semantic_steve import SemanticSteve

from sr_olthad import (
    DomainSpecificSysPromptInputData,
    GetDomainSpecificSysPromptInputData,
    LmAgentName,
    UserPromptInputData,
)

LM_ROLE_AS_VERB_PHRASE = SemanticSteve.get_user_role_as_verb_phrase()
SKILLS_DOCS_STR = "\n\n".join(SemanticSteve.get_skills_docs())
SKILLS_DOCS_INSERT = f"\nHere is the documentation for what skill functions are available to you:\n{SKILLS_DOCS_STR}\n"
DOMAIN_EXPOSITION_TEMPLATE = """You are controlling a Minecraft player using SemanticSteve, a library that wraps playing the game of Minecraft with textual world-state observations and idiomatic "skill"-function calling.
{{ skills_docs }}
Here are some general tips for using SemanticSteve:
- The best way to find things is to think about what is visible in each direction and approach something in the direction that you think is most likely to get you closer to your goals/the things you want to find.
- To dig down, you can call the pathFindToCoordinates function with a y-coordinate that is below your current level. It is recommended that you dig down at (i.e., pick coordinates) at a diagonal angle (and not straight down) to avoid falling into lava or other hazards."""


PLANNER_INSERT = """IMPORTANT: Since you are responsible for creating and updating tentative plans, it is important for you to know that you can and should, at some point (when the level of granularity is appropriately narrow), output tasks that are syntactically-valid function calls to the SemanticSteve skill functions.

For example, if the "task in question" was "gather wood" and an "oak_log" was visible in your immediate surroundings, you probably ought to plan at least a task that is a syntactically-valid invocation of the `mineBlocks` function, e.g., you could output something like `["mineBlocks('oak_log')"]`.

This logic also applies to other skills, such as `craftItems`, `placeBlocks`, and `useItems`. For example, if the "task in question" was "craft 1 furnace from 8 cobblestone" and you had 8 'cobblestone' in your inventory, you could output something like `["craftItems('furnance', 1)"]` due to the skill handling the finer logic.

Remember, however, that you are to break down tasks into further high-level subtasks in open-ended natural language until you reach a situation where it is appropriate to output a skill-function call. E.g., if the "task in question" was to "gather wood", but there were no logs or planks in your surroundings, you break down the task further until you are certain that a function-call is appropriate, e.g., `["explore to find some form of planks or logs", "gather the planks or logs"]`.

Pay attention to the documentation for how to use the functions to make sure you are invoking them correctly in appropriate situations (i.e., when they are likely to succeed). Do not hallicinate functions that are not available to you. Only use the functions that are documented above.

IMPORTANT: If you are interacting with items, the amount of an item you want to craft, place, insert, take, etc., must be explicitly specified in the task. Then, include a total count.
    - Example: If we want to craft 2 blocks, and we have 4 in our inventory, the task is: "Craft 2 blocks". 
    - Example: "Acquire more oak planks" should be "Acquire X oak planks".
    - Example: "do craft oak door from oak planks" should be "Craft 1 door from 6 oak planks".
    - Example: "craft iron nuggets from iron ingots" should be "craft 9 iron nuggets from 1 iron ingot".
    - Example: if we already have 4 planks and need 1 more: "craft 1 planks" should be "craft 1 planks from 1 logs".

IMPORTANT: You define a task as "granular enough" to be a valid skill function call if the task is a single, atomic action that can be performed in the game world. This means that the task should be specific enough to be accomplished with a single function call, without requiring any additional context or information. For example, "mine a block", "craft 3 X's from Y", "place W at x,y,z", "place W", would be considered granular enough to be a valid skill function call, while "gather resources" or "build a house" would not be granular enough.

IMPORTANT: IF THE TASK IN QUESTION IS GRANULAR ENOUGH FOR AN APPROPRIATE NEXT FUNCTION CALL TO BE THE NEXT-MOST PLAN, OUTPUT A VALID SKILL FUNCTION CALL, e.g., if the task was 'get planks' and you had 6 'oak_logs' in your inventory:\n```json\n{\n"new_planned_subtasks": ["craftItems('oak_planks', 24)"]\n}```.

IMPORTANT: If you are describing a task in a manner that includes a skill in a similar manner to: \"Move to <block> using pathfindToBlock("...")\", \"Use pathfindToCoordinate([...]) to move east\", \"pathfind to <block> at coordinates <x,y,z>\", you should instead simply output the function call as a JSON string, e.g., `["pathfindToBlock('dirt')"]`, `["pathfindToCoordinate([12,12,12])"]`. This is because the system will take care of executing the function call for you. You are only responsible for creating and updating the plans at a conservative next-most level of granularity.

IMPORTANT: NEVER output a function call with surrounding text, like \"Execute <function\", \"Perform <function>\", \"Call <function>\", etc. Just output the function call as a JSON string, e.g., `["mineBlocks('oak_log')"]`. The system will take care of executing the function call for you. You are only responsible for creating and updating the plans at a conservative next-most level of granularity."""

# IMPORTANT: If you are crafting, you MUST look up the recipes for the item you are crafting. THERE IS A SKILL PROVIDED FOR THIS.
#     - Example: "craft 1 door from 6 planks" REQUIRES its first subtask to be "getRecipesForItem('door')".
#         - Reasoning: You do not know the recipes for items. The skill will tell you what you need explicitly.
#     - Exception: If they have already been looked up before, you can use the cached recipes. If it was skipped, you may also skip them.
        

ATTEMPT_SUMMARIZER_INSERT = (
    'IMPORTANT: Pay close attention to the "skillInvocationResults" and "inventoryChanges"!'
)


get_semantic_steve_sys_prompt_input_data: GetDomainSpecificSysPromptInputData


def get_semantic_steve_sys_prompt_input_data(
    lm_agent_name: LmAgentName, user_prompt_input_data: UserPromptInputData
) -> DomainSpecificSysPromptInputData:
    # TODO: Dynamically render in situation-relevent tips
    # TODO: Dynamically render in situation-relevent examples

    template: Template = Template(DOMAIN_EXPOSITION_TEMPLATE)
    if lm_agent_name in (LmAgentName.PLANNER, LmAgentName.ATTEMPT_SUMMARIZER):
        domain_exposition = template.render(skills_docs=SKILLS_DOCS_INSERT)
    else:
        domain_exposition = template.render(skills_docs="")

    if lm_agent_name == LmAgentName.PLANNER:
        domain_exposition += "\n\n" + PLANNER_INSERT
    elif lm_agent_name == LmAgentName.ATTEMPT_SUMMARIZER:
        domain_exposition += "\n\n" + ATTEMPT_SUMMARIZER_INSERT

    return DomainSpecificSysPromptInputData(
        lm_role_as_verb_phrase=LM_ROLE_AS_VERB_PHRASE,
        domain_exposition=domain_exposition,
    )
