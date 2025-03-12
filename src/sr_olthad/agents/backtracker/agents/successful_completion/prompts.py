from typing import List

from enums import PromptType
from schema import RegistrablePrompt, PromptRegistry

######################
######## v1.0 ########
######################

SYS_1_0 = """"""
USER_1_0 = """"""

V1_0: List[RegistrablePrompt] = [
    RegistrablePrompt(type=PromptType.SYS, prompt=SYS_1_0),
    RegistrablePrompt(type=PromptType.USER, prompt=USER_1_0),
]

######################
###### Registry ######
######################

PROMPT_REGISTRY: PromptRegistry = {
    "1.0": V1_0,
}
