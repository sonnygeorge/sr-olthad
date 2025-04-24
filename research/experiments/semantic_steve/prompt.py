from jinja2 import Template

from research.experiments.semantic_steve.prompt_inserts import (
    ATTEMPT_SUMMARIZER_INSERT,
    DOMAIN_EXPOSITION_TEMPLATE,
    EXAMPLES_TEMPLATE_STR,
    LM_ROLE_AS_VERB_PHRASE,
    PLANNER_INSERT,
    SKILLS_DOCS_INSERT,
)
from research.experiments.semantic_steve.rag.retrieve import retrieve
from sr_olthad import (
    DomainSpecificSysPromptInputData,
    LmAgentName,
    UserPromptInputData,
)


def get_semantic_steve_sys_prompt_input_data(
    lm_agent_name: LmAgentName, user_prompt_input_data: UserPromptInputData
) -> DomainSpecificSysPromptInputData:
    # TODO: (Dynamically?) render in (situation-relevent) tips?

    main_template: Template = Template(DOMAIN_EXPOSITION_TEMPLATE)
    examples_template: Template = Template(EXAMPLES_TEMPLATE_STR)

    if lm_agent_name in (LmAgentName.PLANNER, LmAgentName.ATTEMPT_SUMMARIZER):
        domain_exposition = main_template.render(skills_docs=SKILLS_DOCS_INSERT)
    else:
        domain_exposition = main_template.render(skills_docs="")

    if lm_agent_name == LmAgentName.PLANNER:
        domain_exposition += "\n\n" + PLANNER_INSERT
        examples = retrieve(2, user_prompt_input_data, LmAgentName.PLANNER)
        examples_str = examples_template.render(examples=examples)
        domain_exposition += "\n\n" + examples_str
    elif lm_agent_name == LmAgentName.ATTEMPT_SUMMARIZER:
        domain_exposition += "\n\n" + ATTEMPT_SUMMARIZER_INSERT

    return DomainSpecificSysPromptInputData(
        lm_role_as_verb_phrase=LM_ROLE_AS_VERB_PHRASE,
        domain_exposition=domain_exposition,
    )
