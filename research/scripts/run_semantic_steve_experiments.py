# Load dotenv BEFORE imports
from dotenv import load_dotenv

load_dotenv()

import asyncio
import csv
import os

from semantic_steve import DataFromMinecraft, SemanticSteve
from semantic_steve.screenshot_steve import (
    TaskRunResult,
    run_and_score_task,
)

from research.experiments.semantic_steve.prompt import (
    get_semantic_steve_sys_prompt_input_data,
)
from research.utils import is_function_call
from sr_olthad import SrOlthad

TASKS = [
    "take a screenshot of some stairs that you placed onto some cobblestone",
    "take a screenshot of an oak trap door that you placed onto coarse dirt",
    "take a screenshot of a button",
    "take a screenshot of a furnace",
    "take a screenshot of 3 cobblestone stacked on top of each other",
]


def append_task_result_to_csv(csv_fpath: str, result: TaskRunResult) -> None:
    should_write_header = False if os.path.isfile(csv_fpath) else True
    # Open in append mode ('a') to add to existing file
    with open(csv_fpath, "a", newline="") as f:
        writer = csv.writer(f)
        if should_write_header:
            headers = list(TaskRunResult.__annotations__.keys())
            writer.writerow(headers)
        writer.writerow(
            [
                result.task,
                result.screenshot_fpath,
                result.score,
                result.n_skills_invoked,
                result.time_elapsed_seconds,
            ]
        )


async def run_one_experiment(
    task: str, csv_fpath: str = "results.csv", screenshot_dir: str = os.getcwd()
) -> None:
    # TODO: Parameterize this fn w/ sr-OLTHAD config?
    sr_olthad = SrOlthad(
        highest_level_task=task,
        is_task_executable_skill_invocation=is_function_call,
        get_domain_specific_sys_prompt_input_data=get_semantic_steve_sys_prompt_input_data,
    )

    async def get_next_skill_invocation(data_from_minecraft: DataFromMinecraft) -> str:
        env_state_str = f"```json\n{data_from_minecraft.get_readable_string()}\n```"
        return await sr_olthad.get_next_skill_invocation(env_state_str)

    semantic_steve = SemanticSteve(screenshot_dir=screenshot_dir)
    result = await run_and_score_task(task, get_next_skill_invocation, semantic_steve)
    print(f"Score for '{task}' was {result.score}.")
    append_task_result_to_csv(csv_fpath, result)
    print(f"Results for '{task}' written to {csv_fpath}.")


if __name__ == "__main__":
    # asyncio.run(run_one_experiment(TASKS[0]))
    asyncio.run(run_one_experiment("Take a screenshot of a grass block"))
