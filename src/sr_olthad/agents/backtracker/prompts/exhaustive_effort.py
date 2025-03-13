from jinja2 import Template

from schema import SingleTurnPromptTemplates, PromptRegistry

######################
######## v1.0 ########
######################

SYS_1_0 = """"""
USER_1_0 = """"""

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
