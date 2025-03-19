import os
import textwrap
from typing import List, Optional

from nicegui import ui

from agent_framework.schema import LmStreamsHandler
from sr_olthad.emissions import (
    PostLmGenerationStepEmission,
    PreLmGenerationStepEmission,
)

# TODO: Loading spinner
# IDEA: Task node update could yield a diff then await a boolean send for whether to commit the pending update
# ...configure whether to do this or not on TaskNode instantiation
# TODO: Change async_call_idx to streams idx

HEADER_HEIGHT_PX = 30
FOOTER_HEIGHT_PX = 80
COL_HEIGHT = f"calc(100vh - {HEADER_HEIGHT_PX + FOOTER_HEIGHT_PX}px)"
COL_WRAP_CHARS = 84


class TextBox(ui.element):
    def __init__(
        self,
        lines: Optional[List[str]] = None,
        is_diff: bool = False,
    ) -> None:
        super().__init__("div")
        self.classes("w-full")
        self.is_diff = is_diff
        if lines is not None:
            self.reset(lines)

    def reset(self, lines: List[str]) -> None:
        self.clear()
        html = '<pre style="font-family: monospace; line-height: 0.78em;">'
        for line in lines:
            if self.is_diff or len(line) < COL_WRAP_CHARS:
                sublines = [line]
            else:
                sublines = textwrap.wrap(line, COL_WRAP_CHARS)
            for subln in sublines:
                if subln[-1] != "\n":
                    subln += "\n"
                if self.is_diff:
                    if subln.startswith("- "):
                        html += f'<span style="color: #ff4444">{subln}</span>'
                    elif subln.startswith("+ "):
                        html += f'<span style="color: #44ff44">{subln}</span>'
                    elif subln.startswith("? "):
                        html += f'<span style="color: #888888">{subln}</span>'
                    else:
                        html += f'<span style="color: #ffffff">{subln}</span>'
                else:
                    html += f'<span style="color: #ffffff">{subln}</span>'
        html += "</pre>"
        with self:
            ui.html(html).classes("p-2 text-white")

    def append_chunk(self, chunk: str) -> None:
        pass  # TODO


class IsExecutableActionDialog(ui.dialog):
    def __init__(self):
        super().__init__()
        with self, ui.card():
            self.question = ui.label()
            with ui.row():
                self.switch = ui.switch(
                    value=False, on_change=self.toggle_switch_label
                )
                self.switch_label = ui.label("No")
            self.submit_btn = ui.button("Submit", on_click=self.close)

    def toggle_switch_label(self):
        self.switch_label.set_text("Yes" if self.switch.value else "No")

    async def classify(self, task_to_classify: str) -> bool:
        self.question.set_text(f"Is {task_to_classify} an executable action?")
        super().open()
        await self.submit_btn.clicked()
        super().close()
        return self.switch.value


class GetEnvStateDialog(ui.dialog):
    def __init__(self):
        super().__init__()
        with self, ui.card():
            self.action = ui.label()
            self.env_state_input = ui.textarea("Resulting env state:")
            self.submit_btn = ui.button("Submit", on_click=self.close)

    async def get_env_state(self, action: Optional[str]) -> str:
        if action is None:
            action = "(none yet)"
        self.action.set_text(f"ACTION: {action}")
        super().open()
        await self.submit_btn.clicked()
        super().close()
        return self.env_state_input.value


def add_styles():
    ui.dark_mode().enable()
    styles_fpath = os.path.join(os.path.dirname(__file__), "styles.css")
    with open(styles_fpath, "r") as f:
        styles = f.read()
    ui.add_head_html(f"<style>{styles}</style>")


def header() -> ui.header:
    header = ui.header().style(f"height: {HEADER_HEIGHT_PX}px;")
    header.style("background-color: #040527")
    return header.classes("p-0 gap-0 items-center")


def footer() -> ui.footer:
    footer = ui.footer().style(f"height: {FOOTER_HEIGHT_PX}px;")
    footer.style("background-color: #040527")
    return footer.classes("bg-gray-900 p-0 gap-0 items-start")


class GuiApp:
    OLTHAD_UPDATE_LABEL_FSTR = "Pending OLTHAD Update⠀⠀⠀(cur node={task_id})"
    CUR_AGENT_LABEL_FSTR = "Current Agent: {agent_name}"

    def __init__(self):
        add_styles()
        self.get_env_state = GetEnvStateDialog().get_env_state
        self.classify_executable_action = IsExecutableActionDialog().classify
        self.lm_response_text_boxes = []

        # Header
        with header():
            with ui.row().classes("w-1/3 justify-center"):
                ui.label("Input Prompt Used")
            with ui.row().classes("w-1/3 justify-center"):
                ui.label("LM Response(s)")
            with ui.row().classes("w-1/3 justify-center"):
                self.olthad_update_label = ui.label()

        # Columns
        content = ui.element("div").classes("c-columns bg-gray-900")
        with content:
            prompt_col = ui.element("div").classes("c-column left")
            with prompt_col.style(f"height: {COL_HEIGHT}"):
                self.prompt_col_text_box = TextBox()
            lm_responses_col = ui.element("div").classes("c-column middle")
            lm_responses_col.style(f"height: {COL_HEIGHT}")
            olthad_update_col = ui.element("div").classes("c-column right")
            with olthad_update_col.style(f"height: {COL_HEIGHT}"):
                self.olthad_update_col_text_box = TextBox(is_diff=True)

        # Footer
        with footer():
            with ui.row().classes("w-1/3 justify-center pt-4"):
                self.cur_agent_label = ui.label()
            with ui.row().classes("w-1/3 justify-center"):
                pass  # Nothing in the middle
            with ui.row().classes("w-1/3 justify-center pt-4"):
                accept_btn = ui.button(text="Accept & Proceed")
                accept_btn.props("color=green size=lg").classes("w-2/5")
                reject_btn = ui.button(text="Run This Step Again")
                reject_btn.props("color=red size=lg").classes("w-2/5")

    @property
    def handle_streams(self) -> LmStreamsHandler:
        """Streams handler to append chunks to GUI's LM response text boxes."""

        # NOTE: This has to inherit from LmStreamsHandler ABC
        class HandleStreams(LmStreamsHandler):
            def __call__(
                _, chunk_str: str, async_call_idx: Optional[int] = None
            ) -> None:
                text_box = self.lm_response_text_boxs[async_call_idx]
                text_box.append_chunk(chunk_str)

        return HandleStreams()

    async def handle_pre_generation_event(
        self, emission: PreLmGenerationStepEmission
    ) -> None:
        # Update the right column header
        # Update the current agent label
        # Update the prompt column text with prompt messages
        # Empty the OLTHAD update column text
        self.olthad_update_col_text_box.reset([])
        # Update LM response column
        # with lm_responses_col:
        #     ui.separator()
        #     for _ in range(7):
        #         box = ui.element("div").classes("c-row")
        #         with box:
        #             Text(TEXT1.splitlines(keepends=True))
        #         ui.separator()
        # Return stream handlers

    async def handle_post_generation_event(
        self, emission: PostLmGenerationStepEmission
    ) -> bool:
        # TODO: Do something with this for annotation
        # emission.messages

        # Update OLTHAD update columns text
        pre_update_olthad_str = emission.pre_update_olthad.stringify()
        post_update_olthad_str = emission.post_olthad_update.stringify()
        diff = self.differ.compare(
            pre_update_olthad_str.splitlines(keepends=True),  # FIXME
            post_update_olthad_str.splitlines(keepends=True),
        )
        self.olthad_update_col_text_box.reset(list(diff))

        # Await user to indicate acceptance or rejection of the OLTHAD update
