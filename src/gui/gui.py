import difflib
import os
import textwrap
from typing import List

from nicegui import ui

# TODO: Remove stream handlers from sr-OLTHAD...? !!


HEADER_HEIGHT_PX = 30
FOOTER_HEIGHT_PX = 80
COL_HEIGHT = f"calc(100vh - {HEADER_HEIGHT_PX + FOOTER_HEIGHT_PX}px)"
TEXT1 = """
[
  '{{repeat(5, 7)}}',
  {
    _id: '{{objectId()}}',
    index: '{{index()}}',
    guid: '{{guid()}}',
    isActive: '{{bool()}}',
    balance: '{{floating(1000, 4000, 2, "$0,0.00")}}',
    picture: 'http://placehold.it/32x32',
    age: '{{integer(20, 40)}}',
    eyeColor: '{{random("blue", "brown", "green")}}',
    company: '{{company().toUpperCase()}}',
    email: '{{email()}}',
    phone: '+1 {{phone()}}',
    address: '{{integer(100, 999)}} {{street()}}, {{city()}}, {{state()}}, {{integer(100, 10000)}}',
    about: '{{lorem(1, "paragraphs")}}',
    registered: '{{date(new Date(2014, 0, 1), new Date(), "YYYY-MM-ddThh:mm:ss Z")}}',
    latitude: '{{floating(-90.000001, 90)}}',
    longitude: '{{floating(-180.000001, 180)}}',
    tags: [
      '{{repeat(7)}}',
      '{{lorem(1, "words")}}'
    ],
    friends: [
      '{{repeat(3)}}',
      {
        id: '{{index()}}',
        name: '{{firstName()}} {{surname()}}'
      }
    ],
    greeting: function (tags) {
      return 'Hello, ' + this.name + '! You have ' + tags.integer(1, 10) + ' unread messages.';
    },
    favoriteFruit: function (tags) {
      var fruits = ['apple', 'banana', 'strawberry'];
      return fruits[tags.integer(0, fruits.length - 1)];
    }
  }
]
"""
TEXT2 = """
[
  '{{repeat(5, 7)}}',
  {
    _id: '{{objectId()}}',
    index: '{{index()}}',
    guid: '{{guid()}}',
    isActive: '{{bool()}}',
    balance: '{{floating(1000, 4000, 2, "$0,0.00")}}',
    picture: 'http://placehold.it/32x32',
    age: '{{integer(20, 40)}}',
    eyeColor: '{{random("blue", "brown", "green")}}',
    name: '{{firstName()}} {{surname()}}',
    gender: '{{gender()}}',
    company: '{{company().toUpperCase()}}',
    email: '{{email()}}',
    phone: '+1 {{phone()}}',
    address: '{{integer(100, 999)}} {{street()}}, {{city()}}, {{state()}}, {{integer(100, 10000)}}',
    about: '{{lorem(1, "paragraphs")}}',
    registered: '{{date(new Date(2014, 0, 1), new Date(), "YYYY-MM-ddThh:mm:ss Z")}}',
    latitude: '{{floating(-90.000001, 90)}}',
    tags: [
      '{{repeat(7)}}',
      '{{lorem(1, "words")}}'
    ],
    friends: [
      '{{repeat(3)}}',
      {
        id: '{{index()}}',
        name: '{{firstName()}} {{surname()}}'
      }
    ],
    greeting: function (tags) {
      return 'Hello, ' + this.name + '! You have ' + tags.integer(1, 10) + ' unread messages.';
    },
    favoriteFruit: function (tags) {
      var fruits = ['apple', 'banana', 'strawberry'];
      return fruits[tags.integer(0, fruits.length - 1)];
    }
  }
]
"""
COL_WRAP_CHARS = 84


class Text(ui.element):
    def __init__(
        self,
        lines: List[str],
        is_diff: bool = False,
    ) -> None:
        super().__init__("div")
        self.classes("w-full")
        self.is_diff = is_diff
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


def run():
    ui.dark_mode().enable()

    # Add stylesheet
    styles_fpath = os.path.join(os.path.dirname(__file__), "styles.css")
    with open(styles_fpath, "r") as f:
        styles = f.read()
    ui.add_head_html(f"<style>{styles}</style>")

    # Header
    header = (
        ui.header()
        .style(f"height: {HEADER_HEIGHT_PX}px;")
        .classes("p-0 gap-0 items-center")
    )
    header.style("background-color: #040527")
    with header.classes("p-0 gap-0 items-center"):
        with ui.row().classes("w-1/3 justify-center"):
            ui.label("Input Prompt Used")
        with ui.row().classes("w-1/3 justify-center"):
            ui.label("LM Response(s)")
        with ui.row().classes("w-1/3 justify-center"):
            ui.label("Pending OLTHAD Update⠀⠀⠀(cur node=1.1.2.1.3)")

    # Content
    content = ui.element("div").classes("c-columns bg-gray-900")
    with content:
        left_col = ui.element("div")
        left_col.classes("c-column left").style(f"height: {COL_HEIGHT}")

        middle_col = ui.element("div")
        middle_col.classes("c-column middle").style(f"height: {COL_HEIGHT}")

        right_col = ui.element("div")
        right_col.classes("c-column right").style(f"height: {COL_HEIGHT}")

    with left_col:
        Text(TEXT1.splitlines(keepends=True))

    with middle_col:
        ui.separator()
        for _ in range(7):
            box = ui.element("div").classes("c-row")
            with box:
                Text(TEXT1.splitlines(keepends=True))
            ui.separator()

    diff = list(
        difflib.Differ().compare(
            TEXT1.splitlines(keepends=True), TEXT2.splitlines(keepends=True)
        )
    )

    with right_col:
        Text(diff, is_diff=True)

    # Footer
    footer = ui.footer().style(f"height: {FOOTER_HEIGHT_PX}px")
    footer.style("background-color: #040527")
    with footer.classes("bg-gray-900 p-0 gap-0 items-start"):
        with ui.row().classes("w-1/3 justify-center pt-4"):
            ui.label("Current Agent: Backtracker")
        with ui.row().classes("w-1/3 justify-center"):
            env_state_input = ui.textarea("Resulting env state:")
            env_state_input.props("dense standout").classes("m-4 w-full")
        with ui.row().classes("w-1/3 justify-center pt-4"):
            accept_btn = ui.button(text="Accept & Proceed")
            accept_btn.props("color=green size=lg").classes("w-2/5")
            reject_btn = ui.button(text="Run This Step Again")
            reject_btn.props("color=red size=lg").classes("w-2/5")

    # Run the UI
    ui.run(title="sr-OLTHAD")
