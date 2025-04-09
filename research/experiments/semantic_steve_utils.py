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
"""

get_semantic_steve_sys_prompt_input_data: GetDomainSpecificSysPromptInputData


def get_semantic_steve_sys_prompt_input_data(
    lm_agent_name: LmAgentName, user_prompt_input_data: UserPromptInputData
) -> DomainSpecificSysPromptInputData:
    return DomainSpecificSysPromptInputData(
        lm_role_as_verb_phrase=LM_ROLE_AS_VERB_PHRASE,
        # TODO: Dynamically render in situation-relevent tips
        # TODO: Dynamically render in situation-relevent examples
        domain_exposition=DOMAIN_EXPOSITION_TEMPLATE,
    )
