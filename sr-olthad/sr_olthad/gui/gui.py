import os
import textwrap

from nicegui import html, ui

from sr_olthad.framework.schema import InstructLmMessage, LmStreamsHandler
from sr_olthad.lm_step import PostLmStepEmission, PreLmStepEmission

HEADER_HEIGHT_PX = 30
FOOTER_HEIGHT_PX = 80
COL_HEIGHT = f"calc(100vh - {HEADER_HEIGHT_PX + FOOTER_HEIGHT_PX}px)"
COL_WRAP_CHARS = 84


# TODO: Implement line-wrapping w/ COL_WRAP_CHARS for streaming LM Responses.


class TextBox(ui.element):
    def __init__(
        self,
        lines: list[str] | None = None,
        is_diff: bool = False,
    ) -> None:
        super().__init__("div")

        self.is_diff = is_diff
        self.lines = []
        self.spans = []

        with self:
            self.pre = ui.element("pre").classes("p-2")
        self.pre.style("font-family: monospace; line-height: 0.70em;")

        if lines is not None:
            self.reset(lines)

    def reset(self, lines: list[str] | None = None) -> None:
        self.pre.clear()
        if lines is None:
            return
        self.lines = []
        self.spans = []
        with self.pre:
            for line in lines:
                if self.is_diff or len(line) < COL_WRAP_CHARS:
                    sublines = [line]
                else:
                    sublines = textwrap.wrap(line, COL_WRAP_CHARS)
                for subln in sublines:
                    if not subln or subln[-1] != "\n":
                        subln += "\n"
                    if self.is_diff:
                        if subln.startswith("- "):
                            span = html.span(subln).style("color: #ff4444")
                        elif subln.startswith("+ "):
                            span = html.span(subln).style("color: #44ff44")
                        elif subln.startswith("? "):
                            span = html.span(subln).style("color: #888888")
                        else:
                            span = html.span(subln).style("color: #ffffff")
                    else:
                        span = html.span(subln).style("color: #ffffff")
                    self.lines.append(subln)
                    self.spans.append(span)

    def append_chunk(self, chunk: str) -> None:
        with self.pre:
            html.span(chunk).style("color: #ffffff")


class IsExecutableActionDialog(ui.dialog):
    def __init__(self):
        super().__init__()

        with self, ui.card():
            self.question = ui.label()
            with ui.row():
                self.switch = ui.switch(value=False, on_change=self.toggle_switch_label)
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

        with self, ui.card().classes("w-1/2 justify-center items-center"):
            self.action = ui.label()
            self.env_state_input = ui.textarea("(Resulting) env state:")
            self.env_state_input.classes("w-full")
            self.submit_btn = ui.button("Submit", on_click=self.close)
            self.submit_btn.props("size=lg")

    async def get_env_state_from_user(self, action: str | None) -> str:
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
    with open(styles_fpath) as f:
        styles = f.read()
    ui.add_head_html(f"<style>{styles}</style>")


def header() -> ui.header:
    header_ = ui.header().style(f"height: {HEADER_HEIGHT_PX}px;")
    header_.style("background-color: #040527")
    return header_.classes("p-0 gap-0 items-center")


def footer() -> ui.footer:
    footer_ = ui.footer().style(f"height: {FOOTER_HEIGHT_PX}px;")
    footer_.style("background-color: #040527")
    return footer_.classes("bg-gray-900 p-0 gap-0 items-start")


def stringify_instruct_lm_messages(messages: list[InstructLmMessage]) -> str:
    output_str = ""
    for msg in messages:
        output_str += "―" * COL_WRAP_CHARS + "\n"
        output_str += f"{msg['role'].upper()}:\n"
        output_str += "―" * COL_WRAP_CHARS + "\n\n"
        output_str += msg["content"] + "\n\n"
    return output_str.strip()


class GuiApp:
    OLTHAD_UPDATE_LABEL_FSTR = "Pending OLTHAD Update⠀⠀(cur node={task_id})"
    CUR_AGENT_LABEL_FSTR = "Current Agent = {lm_agent_name}"

    def __init__(self):
        super().__init__()

        add_styles()
        self.get_env_state_from_user = GetEnvStateDialog().get_env_state_from_user
        self.classify_task_executability = IsExecutableActionDialog().classify
        self.lm_response_text_boxes: list[TextBox] = []

        # Header
        with header():
            with ui.row().classes("w-1/3 justify-center"):
                ui.label("Input Prompt Used")
            with ui.row().classes("w-1/3 justify-center"):
                ui.label("LM Response(s)")
            with ui.row().classes("w-1/3 justify-center"):
                self.olthad_update_label = ui.label()

        # Columns
        self.content = ui.element("div").classes("c-columns bg-gray-900")
        with self.content:
            prompt_col = ui.element("div").classes("c-column left")
            with prompt_col.style(f"height: {COL_HEIGHT}"):
                self.prompt_col_text_box = TextBox()
            self.lm_response_col = ui.element("div").classes("c-column middle")
            self.lm_response_col.style(f"height: {COL_HEIGHT}")
            olthad_update_col = ui.element("div").classes("c-column right")
            with olthad_update_col.style(f"height: {COL_HEIGHT}"):
                self.olthad_update_col_text_box = TextBox(is_diff=True)

        # Footer
        with footer():
            with ui.row().classes("w-1/3 justify-center pt-4"):
                self.cur_agent_label = ui.label()
            with ui.row().classes("w-1/3 justify-center pt-4"):
                # Added the auto-accept toggle in the middle section
                self.auto_accept_switch = ui.switch(
                    "Auto Accept",
                    value=False,  # Off by default
                ).props("color=blue")
            with ui.row().classes("w-1/3 justify-center pt-4 align-start"):
                with ui.row().classes("w-3/5 justify-between"):
                    self.accept_switch = ui.switch(
                        "Accept",
                        value=True,
                        on_change=self.toggle_accept_switch_label,
                    ).props("color=green")
                    self.submit_btn = ui.button("Proceed").classes("w-1/2")
                    self.submit_btn.props("color=green size=lg")

    def toggle_accept_switch_label(self):
        self.submit_btn.set_text("Proceed" if self.accept_switch.value else "Run Step Again")
        self.submit_btn.props(f"color={'green' if self.accept_switch.value else 'red'}")
        self.submit_btn.update()
        self.accept_switch.props(f"color={'green' if self.accept_switch.value else 'red'}")
        self.accept_switch.update()
        self.accept_switch.set_text("Accept" if self.accept_switch.value else "Reject")

    @property
    def handle_streams(self) -> LmStreamsHandler:
        """Streams handler to append chunks to GUI's LM response text boxes."""

        # NOTE: This has to inherit from LmStreamsHandler ABC
        class HandleStreams(LmStreamsHandler):
            def __call__(_, chunk_str: str, stream_idx: int | None = None) -> None:
                if stream_idx is None:
                    stream_idx = 0
                text_box = self.lm_response_text_boxes[stream_idx]
                text_box.append_chunk(chunk_str)

        return HandleStreams()

    async def handle_pre_generation_event(self, emission: PreLmStepEmission) -> None:
        # Update the right column header
        self.olthad_update_label.set_text(
            self.OLTHAD_UPDATE_LABEL_FSTR.format(task_id=emission.cur_node_id)
        )
        # Update the current agent label
        self.cur_agent_label.set_text(
            self.CUR_AGENT_LABEL_FSTR.format(lm_agent_name=emission.lm_agent_name)
        )
        # Update the prompt column text with prompt messages
        msgs_str = stringify_instruct_lm_messages(emission.input_messages)
        self.prompt_col_text_box.reset(msgs_str.split("\n"))

        # Only clear the OLTHAD update column text if we have new content to display
        # (Don't clear it during pre-generation, this will happen in approve_lm_step when new content is available)

        # Update LM response columns to have enough text boxes for streams
        self.lm_response_col.clear()
        self.lm_response_text_boxes = []
        with self.lm_response_col:
            ui.separator()
            for _ in range(emission.n_streams_to_handle):
                container = ui.element("div").classes("c-row")
                with container:
                    text_box = TextBox()
                self.lm_response_text_boxes.append(text_box)
                ui.separator()

    async def handle_lm_retry(self, idx: int, msg: str) -> None:
        with self.content:
            ui.notify(msg, type="warning")
        self.lm_response_text_boxes[idx].reset()

    async def approve_lm_step(self, emission: PostLmStepEmission) -> bool:
        # Update OLTHAD update columns text only when we have new content
        if emission.diff:
            self.olthad_update_col_text_box.reset(emission.diff)

        # If auto-accept is enabled, return the value of the accept switch without waiting for button click
        if self.auto_accept_switch.value:
            return self.accept_switch.value

        # Otherwise, await user to indicate acceptance or rejection of the OLTHAD update
        await self.submit_btn.clicked()
        return self.accept_switch.value
