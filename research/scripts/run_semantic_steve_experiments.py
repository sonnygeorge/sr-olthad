# Load dotenv BEFORE imports
from dotenv import load_dotenv

load_dotenv()

import asyncio
import os
from datetime import datetime, timedelta
from functools import partial

from semantic_steve import SemanticSteve

from research.experiments.semantic_steve.get_prompt_input import (
    get_semantic_steve_sys_prompt_input_data,
)
from research.experiments.semantic_steve.get_task_score import get_task_score
from research.experiments.semantic_steve.utils import (
    TaskRunResult,
    append_task_result_to_csv,
    get_latest_png_in_dir,
)
from research.utils import is_function_call
from sr_olthad import SrOlthad

CUR_DIR = os.path.dirname(os.path.abspath(__file__))
EXPERIMENTS_DIR = os.path.join(CUR_DIR, "../", "experiments")
SEMANTIC_STEVE_DIR = os.path.join(EXPERIMENTS_DIR, "semantic_steve")
assert os.path.isdir(SEMANTIC_STEVE_DIR)
SCREENSHOT_DIR_PATH = os.path.join(SEMANTIC_STEVE_DIR, "screenshots")
RESULTS_CSV_NAME_FORMAT = "results_{start_datetime}.csv"
RESULTS_CSV_DIR = os.path.join(SEMANTIC_STEVE_DIR, "results")
N_SCORES_TO_AVERAGE = 3


async def run_experiment(
    task: str,
    time_limit: timedelta = timedelta(minutes=45),
    n_few_shot_examples_to_use: int = 2,
    results_csv_fpath: str = os.path.join(RESULTS_CSV_DIR, "results.csv"),
) -> None:
    # Set up interfaces
    get_domain_prompt_input_data = partial(
        get_semantic_steve_sys_prompt_input_data,
        n_few_shot_examples=n_few_shot_examples_to_use,
    )
    sr_olthad = SrOlthad(
        highest_level_task=task,
        is_task_executable_skill_invocation=is_function_call,
        get_domain_specific_sys_prompt_input_data=get_domain_prompt_input_data,
    )
    semantic_steve = SemanticSteve(screenshot_dir=SCREENSHOT_DIR_PATH)

    # Main loop to run the experiment
    n_skills_invoked = 0
    start = datetime.now()
    with semantic_steve as ss:
        data_from_minecraft = await ss.wait_for_data_from_minecraft()
        while True:
            if datetime.now() - start > time_limit:
                print("Time limit exceeded.")
                break
            env_state_str = f"```json\n{data_from_minecraft.get_readable_string()}\n```"
            skill_invocation = await sr_olthad.get_next_skill_invocation(env_state_str)
            if skill_invocation is None:
                print("Task completed or dropped.")
                break
            n_skills_invoked += 1
            data_from_minecraft = await ss.invoke(skill_invocation)
    end = datetime.now()

    # Score the resulting screenshot
    screenshot_fname = get_latest_png_in_dir(SCREENSHOT_DIR_PATH, since_datetime=start)
    if screenshot_fname is not None:
        print(f"Scoring the screenshot: {screenshot_fname}")
        screenshot_fname = os.path.join(SCREENSHOT_DIR_PATH, screenshot_fname)
        scores = []
        for _ in range(N_SCORES_TO_AVERAGE):
            scores.append(get_task_score(screenshot_fname, task))
        score = sum(scores) / len(scores)
    else:
        score = 0.0

    # Save the results
    result = TaskRunResult(
        task=task,
        screenshot_fpath=screenshot_fname,
        score=score,
        n_skills_invoked=n_skills_invoked,
        time_elapsed_seconds=(end - start).total_seconds(),
    )
    print(f"Score for '{task}' was {result.score}.")
    append_task_result_to_csv(results_csv_fpath, result)
    print(f"Results for '{task}' written to {results_csv_fpath}.")


if __name__ == "__main__":
    # Since trap doors don't render properly with prismarine-viewer,
    # set env var USE_COMPUTER_CONTROL_FOR_SCREENSHOT to true
    os.environ["USE_COMPUTER_CONTROL_FOR_SCREENSHOT"] = "true"

    n_times_to_run_each_experiment = 3

    start_datetime_str = datetime.now().strftime("%y-%m-%d_%I-%M%p").lower()
    results_csv_fname = RESULTS_CSV_NAME_FORMAT.format(start_datetime=start_datetime_str)
    results_csv_fpath = os.path.join(RESULTS_CSV_DIR, results_csv_fname)
    run_experiment = partial(run_experiment, results_csv_fpath=results_csv_fpath)

    trap_door_task = "take a screenshot of a trap door"
    stairs_task = "take a screenshot of some stairs that you placed onto some cobblestone"
    furnace_task = "take a screenshot of smooth stone placed adjacent to a furnace"

    experiments = [
        ######################################
        ## Take a screenshot of a trap door ##
        ######################################
        # ========================
        # w/out few-shot examples
        # ========================
        partial(run_experiment, task=trap_door_task, n_few_shot_examples_to_use=0),
        partial(run_experiment, task=trap_door_task, n_few_shot_examples_to_use=0),
        partial(run_experiment, task=trap_door_task, n_few_shot_examples_to_use=0),
        # ========================
        # w few-shot examples
        # ========================
        partial(run_experiment, task=trap_door_task, n_few_shot_examples_to_use=2),
        partial(run_experiment, task=trap_door_task, n_few_shot_examples_to_use=2),
        partial(run_experiment, task=trap_door_task, n_few_shot_examples_to_use=2),
        ############################################################################
        ## Take a screenshot of some stairs that you placed onto some cobblestone ##
        ############################################################################
        # ========================
        # w/out few-shot examples
        # ========================
        partial(run_experiment, task=stairs_task, n_few_shot_examples_to_use=0),
        partial(run_experiment, task=stairs_task, n_few_shot_examples_to_use=0),
        partial(run_experiment, task=stairs_task, n_few_shot_examples_to_use=0),
        # ========================
        # w few-shot examples
        # ========================
        partial(run_experiment, task=stairs_task, n_few_shot_examples_to_use=3),
        partial(run_experiment, task=stairs_task, n_few_shot_examples_to_use=3),
        partial(run_experiment, task=stairs_task, n_few_shot_examples_to_use=3),
        ####################################################################
        ## Take a screenshot of smooth stone placed adjacent to a furnace ##
        ####################################################################
        # ========================
        # w/out few-shot examples
        # ========================
        partial(run_experiment, task=furnace_task, n_few_shot_examples_to_use=0),
        partial(run_experiment, task=furnace_task, n_few_shot_examples_to_use=0),
        partial(run_experiment, task=furnace_task, n_few_shot_examples_to_use=0),
        # ========================
        # w few-shot examples
        # ========================
        partial(run_experiment, task=furnace_task, n_few_shot_examples_to_use=3),
        partial(run_experiment, task=furnace_task, n_few_shot_examples_to_use=3),
        partial(run_experiment, task=furnace_task, n_few_shot_examples_to_use=3),
    ]

    for i, run_experiment_func in enumerate(experiments):
        print("Please set up the Minecraft world for the next experiment.")
        print("Press Enter when ready...")
        input()
        print(f"Running experiment #{i + 1}...")
        asyncio.run(run_experiment_func())
        print(f"Experiment {i + 1} of {n_times_to_run_each_experiment} done.")
