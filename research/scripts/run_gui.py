# Load dotenv BEFORE imports
from dotenv import load_dotenv

load_dotenv()


from nicegui import app, ui

from sr_olthad import DomainSpecificSysPromptInputData, SrOlthad
from sr_olthad.gui.gui import GuiApp

gui_app = GuiApp()


ROLE_VERB_PHRASE = "controls a Dungeons and Dragons character"
DOMAIN_EXPOSITION = "You control the character Sir Olthad, a level 1 human wizard."
HIGHEST_LEVEL_TASK = "Save Brandeir from the curse of Blackmoor."


def get_sys_prompt_input_data(*args, **kwargs) -> DomainSpecificSysPromptInputData:
    return DomainSpecificSysPromptInputData(
        lm_role_as_verb_phrase=ROLE_VERB_PHRASE, domain_exposition=DOMAIN_EXPOSITION
    )


async def run_sr_olthad_with_semantic_steve_and_gui():
    sr_olthad = SrOlthad(
        highest_level_task=HIGHEST_LEVEL_TASK,
        is_task_executable_skill_invocation=gui_app.classify_task_executability,
        pre_lm_step_handler=gui_app.handle_pre_generation_event,
        lm_retry_handler=gui_app.handle_lm_retry,
        post_lm_step_approver=gui_app.approve_lm_step,
        get_domain_specific_sys_prompt_input_data=get_sys_prompt_input_data,
        streams_handler=gui_app.handle_streams,
    )

    skill_invocation = None
    while True:
        env_state = await gui_app.get_env_state_from_user(skill_invocation)
        skill_invocation = await sr_olthad.get_next_skill_invocation(env_state)
        if skill_invocation is None:
            print("Root task completed or dropped")
            break


@app.on_startup
async def startup_actions():
    await run_sr_olthad_with_semantic_steve_and_gui()


# Run the UI
ui.run(title="sr-OLTHAD", port=8080, reload=False)
