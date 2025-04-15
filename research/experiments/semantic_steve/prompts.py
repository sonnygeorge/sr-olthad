from semantic_steve import SemanticSteve

from sr_olthad import (
    DomainSpecificSysPromptInputData,
    GetDomainSpecificSysPromptInputData,
    LmAgentName,
    UserPromptInputData,
)

LM_ROLE_AS_VERB_PHRASE = SemanticSteve.get_user_role_as_verb_phrase()
SKILLS_DOCS_STR = "\n\n".join(SemanticSteve.get_skills_docs())
DOMAIN_EXPOSITION_TEMPLATE = f"""You are controlling a Minecraft player using SemanticSteve, a library that wraps playing the game of Minecraft with textual world-state observations and idiomatic "skill"-function calling.

Here is the documentation for all usable SemanticSteve skill functions:
{SKILLS_DOCS_STR}

Here are some general tips for using SemanticSteve:
- The best way to find things is to think about what is visible in each direction and approach something in the direction that you think is most likely to get you closer to your goals/the things you want to find.
- To dig down, you can call the pathFindToCoordinates function with a y-coordinate that is below your current level. It is recommended that you dig down at (i.e., pick coordinates) at a diagonal angle (and not straight down) to avoid falling into lava or other hazards."""


PLANNER_INSERT = """IMPORTANT: Since you are responsible for creating and updating tentative plans, it is important for you to know that you can and should, at some point (when the level of granularity is appropriately narrow), output tasks that are syntactically-valid function calls to the SemanticSteve skill functions.

For example, if the "task in question" was "gather wood" and an "oak_log" was visible in your immediate surroundings, you probably ought to plan at least a task that is a syntactically-valid invocation of the `mineBlocks` function, e.g., you could output something like `["mineBlocks('oak_log')"]`.

Remember, however, that you are to break down tasks into further high-level subtasks in open-ended natural language until you reach a situation where it is appropriate to output a skill-function call. E.g., if the "task in question" was to "gather wood", but there were no logs or planks in your surroundings, you break down the task further until you are certain that a function-call is appropriate, e.g., `["explore to find some form of planks or logs", "gather the planks or logs"]`.

Pay attention to the documentation for how to use the functions to make sure you are invoking them correctly in appropriate situations (i.e., when they are likely to succeed). Do not hallicinate functions that are not available to you. Only use the functions that are documented above."""

ATTEMPT_SUMMARIZER_INSERT = (
    'IMPORTANT: Pay close attention to the "skillInvocationResults" and "inventoryChanges"!'
)


get_semantic_steve_sys_prompt_input_data: GetDomainSpecificSysPromptInputData


def get_semantic_steve_sys_prompt_input_data(
    lm_agent_name: LmAgentName, user_prompt_input_data: UserPromptInputData
) -> DomainSpecificSysPromptInputData:
    # TODO: Dynamically render in situation-relevent tips
    # TODO: Dynamically render in situation-relevent examples
    # TODO: Withhold skills docs from agents that don't need to see them
    domain_exposition = DOMAIN_EXPOSITION_TEMPLATE
    if lm_agent_name == LmAgentName.PLANNER:
        domain_exposition += "\n\n" + PLANNER_INSERT
    elif lm_agent_name == LmAgentName.ATTEMPT_SUMMARIZER:
        domain_exposition += "\n\n" + ATTEMPT_SUMMARIZER_INSERT

    return DomainSpecificSysPromptInputData(
        lm_role_as_verb_phrase=LM_ROLE_AS_VERB_PHRASE,
        domain_exposition=domain_exposition,
    )
