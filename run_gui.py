import sys
from functools import partial

from dotenv import load_dotenv
from nicegui import ui

sys.path.append("src")

from gui.gui import GuiApp
from sr_olthad import SrOlthad

load_dotenv()

# Run the UI
gui_app = GuiApp()
ui.run(title="sr-OLTHAD", show=False)


async def main(highest_level_task: str, domain_documentation: str):
    sr_olthad = SrOlthad(
        highest_level_task=highest_level_task,
        domain_documentation=domain_documentation,
        classify_if_task_is_executable_action=gui_app.classify_executable_action,
        pre_lm_generation_step_handler=gui_app.handle_pre_generation_event,
        post_lm_generation_step_approver=gui_app.handle_and_approve_lm_generation_step,
        streams_handler=gui_app.handle_streams,
    )

    # FIXME: Remove this monkey patch
    sr_olthad.has_been_called_at_least_once_before = True

    next_action = None
    while True:
        env_state = await gui_app.get_env_state_from_user(next_action)
        # env_state = "You are standing with a tree right in front of you. You have nothing in your inventory. An appealing village with a blacksmith is visible to the north."
        # env_state = "You're outside in a plains village. YOU HAVE DIAMONDS IN YOUR INVENTORY"
        next_action = await sr_olthad(env_state=env_state)
        if next_action is None:
            break


if __name__ in {"__main__", "__mp_main__"}:
    highest_level_task = "Acquire iron"
    domain_documentation = "You are controlling a player in a vanilla Minecraft survival world that is set to peaceful mode."

    # Run main in NiceGUI event loop
    run_main = partial(main, highest_level_task, domain_documentation)
    ui.timer(0.1, run_main, once=True)
