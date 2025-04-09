from dotenv import load_dotenv
from nicegui import app, ui

load_dotenv()

from sr_olthad import GetDomainSpecificInsert, SrOlthad
from sr_olthad.gui.gui import GuiApp

gui_app = GuiApp()


async def run_sr_olthad(
    highest_level_task: str,
    get_domain_specific_insert: GetDomainSpecificInsert | None = None,
):
    sr_olthad = SrOlthad(
        highest_level_task=highest_level_task,
        is_task_executable_skill_invocation=gui_app.classify_task_executability,
        pre_lm_step_handler=gui_app.handle_pre_generation_event,
        lm_retry_handler=gui_app.handle_lm_retry,
        post_lm_step_approver=gui_app.approve_lm_step,
        get_domain_specific_insert=get_domain_specific_insert,
        streams_handler=gui_app.handle_streams,
    )

    # FIXME: Remove this monkey patch once all agents are implemented
    sr_olthad.has_been_called_at_least_once_before = True

    skill_invocation = None
    while True:
        env_state = await gui_app.get_env_state_from_user(skill_invocation)
        skill_invocation = await sr_olthad.get_next_skill_invocation(env_state)
        if skill_invocation is None:
            break


@app.on_startup
async def startup_actions():
    domain_specific_insert = "You are controlling a player in a vanilla Minecraft survival world that is set to peaceful mode."
    get_domain_specific_insert = lambda _, __: domain_specific_insert  # noqa: E731
    await run_sr_olthad(
        highest_level_task="Acquire iron",
        get_domain_specific_insert=get_domain_specific_insert,
    )


# Run the UI
ui.run(title="sr-OLTHAD")
