# Load dotenv BEFORE imports
from dotenv import load_dotenv

load_dotenv()

from experiments.semantic_steve.prompt import (
    get_semantic_steve_sys_prompt_input_data,
)
from pydantic import BaseModel
from semantic_steve import SemanticSteve

from research.utils import is_function_call
from sr_olthad import LmAgentName, SrOlthad

TASKS = [
    "take a screenshot of some stairs that you placed onto some cobblestone",
    "take a screenshot of an oak trap door that you placed onto coarse dirt",
    "take a screenshot of a button",
    "take a screenshot of a furnace",
    "take a screenshot of 3 cobblestone stacked on top of each other",
]


async def get_vlm_score(screenshot, task):
    pass


class TaskRunResult(BaseModel):
    task: str
    screenshot_fpath: str
    vlm_score: float
    skills_invoked: int
    tokens_used: dict[LmAgentName, int]
    lm_steps_run: dict[LmAgentName, int]


async def run_task(task: str) -> TaskRunResult:
    # TODO: Parameterize this fn w/ sr-OLTHAD config
    # TODO: Move these functions to experiments/semantic_steve
    sr_olthad = SrOlthad(
        highest_level_task=task,
        is_task_executable_skill_invocation=is_function_call,
        get_domain_specific_sys_prompt_input_data=get_semantic_steve_sys_prompt_input_data,
    )

    n_skills_invoked = 0
    with SemanticSteve() as ss:
        data_from_minecraft = await ss.wait_for_data_from_minecraft()
        while True:
            env_state = f"```json\n{data_from_minecraft.get_readable_string()}\n```"
            skill_invocation = await sr_olthad.get_next_skill_invocation(env_state)
            if skill_invocation is None:
                print("Root task completed or dropped")
                break
            n_skills_invoked += 1
            data_from_minecraft = await ss.invoke(skill_invocation)

        # TODO: Get resulting screenshot (if any)
        # TODO: Get vlm score using task and screenshot
        get_vlm_score(None, task)
        # TODO: Get tokens used and lm steps run
        # TODO: Return TaskRunResult
