import sys

from dotenv import load_dotenv

sys.path.append("src")

from gui.gui import run

load_dotenv()

run()
