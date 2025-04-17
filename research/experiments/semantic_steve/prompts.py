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


PLANNER_INSERT = """IMPORTANT: When a subtask aligns with an available function, you must output tasks that are syntactically-valid function calls to the SemanticSteve skill functions.

For example, if the "task in question" was "gather wood" and an "oak_log" was visible in your immediate surroundings, you probably ought to plan at least a task that is a syntactically-valid invocation of the `mineBlocks` function, e.g., you could output something like `["mineBlocks('oak_log')"]`.

Remember, however, that you are to break down tasks into further high-level subtasks in open-ended natural language until you reach a situation where it is appropriate to output a skill-function call. E.g., if the "task in question" was to "gather wood", but there were no logs or planks in your surroundings, you break down the task further until you are certain that a function-call is appropriate, e.g., `["explore to find some form of planks or logs", "gather the planks or logs"]`.

Pay attention to the documentation for how to use the functions to make sure you are invoking them correctly in appropriate situations (i.e., when they are likely to succeed). Do not hallucinate functions that are not available to you. Only use the functions that are documented above.

IMPORTANT: IF THE TASK IN QUESTION IS GRANULAR ENOUGH FOR AN APPROPRIATE NEXT FUNCTION CALL TO BE THE NEXT-MOST PLAN, OUTPUT A VALID SKILL FUNCTION CALL, e.g., if the task was 'get planks' and you had 6 `oak_logs` in your inventory:\n```json\n{\n"new_planned_subtasks": ["craftItems('oak_planks', 24)"]\n}```."""

ATTEMPT_SUMMARIZER_INSERT = 'IMPORTANT: Pay close attention to the "skillInvocationResults" and "inventoryChanges"!'


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
