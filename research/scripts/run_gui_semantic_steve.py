from dotenv import load_dotenv
from nicegui import app, ui
from semantic_steve import SemanticSteve

from research.experiments.semantic_steve_utils import (
    get_semantic_steve_sys_prompt_input_data,
)
from sr_olthad import SrOlthad
from sr_olthad.gui.gui import GuiApp

load_dotenv()

gui_app = GuiApp()


async def run_sr_olthad_with_semantic_steve_and_gui(
    highest_level_task: str,
):
    sr_olthad = SrOlthad(
        highest_level_task=highest_level_task,
        is_task_executable_skill_invocation=gui_app.classify_task_executability,
        pre_lm_step_handler=gui_app.handle_pre_generation_event,
        lm_retry_handler=gui_app.handle_lm_retry,
        post_lm_step_approver=gui_app.approve_lm_step,
        get_domain_specific_sys_prompt_input_data=get_semantic_steve_sys_prompt_input_data,
        streams_handler=gui_app.handle_streams,
    )

    with SemanticSteve(
        # should_rebuild_typescript=True,
        debug=True,  # TODO: Remove
    ) as ss:
        data_from_minecraft = await ss.wait_for_data_from_minecraft()
        while True:
            env_state = f"```json\n{data_from_minecraft.get_readable_string()}\n```"
            skill_invocation = await sr_olthad.get_next_skill_invocation(env_state)
            if skill_invocation is None:
                print("Root task completed or dropped")
                break
            data_from_minecraft = await ss.invoke(skill_invocation)


@app.on_startup
async def startup_actions():
    await run_sr_olthad_with_semantic_steve_and_gui(highest_level_task="Acquire iron")


# Run the UI
ui.run(title="sr-OLTHAD")
