import sys

sys.path.append("src")

from dotenv import load_dotenv
from nicegui import ui

from gui.gui import GuiApp

load_dotenv()

# Run the UI
GuiApp()
ui.run(title="sr-OLTHAD")
