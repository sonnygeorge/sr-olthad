from jinja2 import Template

from schema import SingleTurnPrompts, PromptRegistry

######################
######## v1.0 ########
######################

SYS_1_0 = """"""
USER_1_0 = """"""

V1_0_PROMPTS = SingleTurnPrompts(
    sys_prompt=SYS_1_0,
    user_prompt=Template(USER_1_0),
)

######################
###### Registry ######
######################

PROMPT_REGISTRY: PromptRegistry = {
    "1.0": V1_0_PROMPTS,
}
