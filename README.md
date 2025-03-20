<!--
TODO: Dynamically render sys prompts w/ domain documentation
TODO: Hook up to AlfWorld, TextWorld, SemanticSteve, etc.
TODO: RAG of Domain-specific or -agnostic (SemanticSteve?) 'tutorials'?
TODO: Internal "notepad"
TODO: Rename "GUI" to "dashboard"?
TODO: Think about SemanticSteve Results string?
TODO: Add m-coding style logging
TODO: Ranking of multiple async "Planner" outputs?
-->

# sr-OLTHAD

**S**tructured **R**easoning with **O**pen-**L**anguage **H**ierarchies of **A**ny **D**epth

## How To Run

1. Install the requirements: `pip install -r requirements.txt`
2. Make sure you have an `OPENAI_API_KEY` environment variable: `export OPENAI_API_KEY={your key}` (or add to a .env file that `load_dotenv()` can read)
3. Run the GUI: `python run_gui.py`

## Repo Structure

```python
📦sr-olthad
 ┣ 📂src
 ┃ ┣ 📂agent_framework # Package for generic agent framework
 ┃ ┃ ┣ 📂agents # Package for generic plug-and-play "agents"
 ┃ ┃ ┃ ┗ 📜single_turn_chat.py
 ┃ ┃ ┣ 📜lms.py # Module (soon-to-be package) for a variety of LMs
 ┃ ┃ ┣ 📜schema.py
 ┃ ┃ ┗ 📜utils.py
 ┃ ┃
 ┃ ┣ 📂gui # GUI code
 ┃ ┃
 ┃ ┣ 📂react # Code pertaining to the recreation of another comparable method
 ┃ ┃         # ...(e.g. ReAct prompting)
 ┃ ┃
 ┃ ┗ 📂sr_olthad # Package for sr-OLTHAD
 ┃   ┣ 📂agents # Package for the 4(?) main "agents" of sr-OLTHAD
 ┃   ┃ ┣ 📂attempt_summarizer
 ┃   ┃ ┣ 📂backtracker
 ┃   ┃ ┣ 📂forgetter
 ┃   ┃ ┣ 📂planner
 ┃   ┣ 📜config.py
 ┃   ┣ 📜schema.py
 ┃   ┣ 📜sr_olthad.py # Main sr-OLTHAD class that outer contexts import
 ┃   ┣ 📜olthad.py # Everything OLTHAD: traversal, TaskNode, etc.
 ┃   ┗ 📜utils.py
 ┃
 ┣ 📜quick_tests.py # Ad-hoc testing scripts
 ┣ 📜run_gui.py
 ┗ 📜requirements.txt
```
