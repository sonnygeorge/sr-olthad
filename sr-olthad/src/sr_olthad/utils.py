from typing import TYPE_CHECKING

from sr_olthad.common.schema import InstructLmMessage
from sr_olthad.common.utils import render_single_turn_prompt_templates_and_get_messages
from sr_olthad.registry import LM_AGENT_CONFIGS_REGISTRY, PROMPT_REGISTRIES_REGISTRY
from sr_olthad.schema import (
    BinaryChoiceOptions,
    CommonSysPromptInputData,
    CommonUserPromptInputData,
    LmAgentName,
    NonBinaryChoiceOptions,
)

if TYPE_CHECKING:
    from sr_olthad.lm_step import GetDomainSpecificInsert


def get_input_messages(
    lm_agent_name: LmAgentName,
    user_prompt_input_data: CommonUserPromptInputData,
    get_domain_specific_insert: GetDomainSpecificInsert | None = None,
) -> list[InstructLmMessage]:
    """
    Gets agent prompt templates from the registries and renders necessary data into them.
    """
    cfg = LM_AGENT_CONFIGS_REGISTRY[lm_agent_name]
    prompt_registry = PROMPT_REGISTRIES_REGISTRY[lm_agent_name]

    if get_domain_specific_insert is None:
        sys_prompt_input_data = None
    else:
        sys_prompt_input_data = CommonSysPromptInputData(
            domain_specific_insert=get_domain_specific_insert(
                lm_agent_name, user_prompt_input_data
            ),
        )

    return render_single_turn_prompt_templates_and_get_messages(
        user_prompt_template=prompt_registry[cfg.PROMPTS_VERSION].user_prompt_template,
        user_prompt_input_data=user_prompt_input_data,
        sys_prompt_template=prompt_registry[cfg.PROMPTS_VERSION].sys_prompt_template,
        sys_prompt_input_data=sys_prompt_input_data,
    )


def extract_letter_from_multiple_choice_response(
    text: str,
    options: BinaryChoiceOptions | NonBinaryChoiceOptions,
) -> str:
    """
    Decides what 'letter' option is specified in an associated LM response JSON field
    (i.e., the field that's meant to contain the final answer).
    """
    for option in options.values():
        option_letter_clean = "".join(c for c in option.letter if c.isalpha()).lower()
        option_text_clean = "".join(c for c in option.text if c.isalpha()).lower()
        chosen_clean = "".join(c for c in text if c.isalpha()).lower()
        if option_letter_clean == chosen_clean:
            return option.letter
        if option_text_clean in chosen_clean:
            return option.letter
    # TODO: Fuzzy matching? (possibly... certainly not urgent)... constrained generation?
    raise ValueError("None of the answer choices were found in the text")
