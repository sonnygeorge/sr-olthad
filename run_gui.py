import sys

sys.path.append("src")

from dotenv import load_dotenv
from nicegui import ui

from gui.gui import GuiApp
from sr_olthad import SrOlthad

# from sr_olthad.olthad import TaskNode, TaskStatus


load_dotenv()

# Run the UI
gui_app = GuiApp()

sr_olthad = SrOlthad(
    highest_level_task="Acquire diamonds",
    domain_documentation="Single player minecraft world in peaceful mode.",
    classify_if_task_is_executable_action=gui_app.classify_executable_action,
    pre_lm_generation_step_handler=gui_app.handle_pre_generation_event,
    post_lm_generation_step_handler=gui_app.handle_post_generation_event,
    streams_handler=gui_app.handle_streams,
)

# # FIXME: Remove this monkey patch
sr_olthad.has_been_called_at_least_once_before = True

# env_state = "You are standing with a tree right in front of you. You have nothing in your inventory. An appealing village with a blacksmith is visible to the north."
env_state = (
    "You're outside in a plains village. YOU HAVE DIAMONDS IN YOUR INVENTORY"
)


if __name__ == "__mp_main__":

    async def main_loop():
        while True:
            next_action = await sr_olthad(env_state=env_state)
            print(next_action)

    ui.timer(0.1, main_loop, once=True)


ui.run(title="sr-OLTHAD", show=False)
