<!--
TODO: Make the prompts actually make sense & figure out relationship of either: (1) sys_prompt = f"... {domain_insert}", (2) domain_template = f"... {sys_prompt}", or (3) sys_prompt = "you will be told some stuff about what domain you are acting in and then...", user_prompt = f"{domain_insert}..."
TODO: RAG & Sr-Olthad case-by-case test suite
TODO: Hook up to AlfWorld, TextWorld, SemanticSteve, etc.
TODO: RAG of Domain-specific or -agnostic (SemanticSteve?) 'tutorials'?
TODO: Wrap lines in LM `TextBox`s?
TODO: Internal "notepad"!!
TODO: Rename "GUI" to "dashboard"?
TODO: Think about SemanticSteve Results string?
TODO: Logging?
TODO: Ranking of multiple async "Planner" outputs?
-->

# sr-OLTHAD

**S**tructured **R**easoning With **O**pen-**L**anguage **H**ierarchies of **A**ny **D**epth

## How To Run

1. Install the requirements: `pip install -r requirements.txt`
2. Make sure you have an `OPENAI_API_KEY` environment variable: `export OPENAI_API_KEY={your key}` (or add to a .env file that `load_dotenv()` can read)
3. Run the GUI: `python run_gui.py`

## Repo Structure

```python
📦sr-olthad
 ┣ 📂src
 ┃ ┣ 📂agent_framework # Package for generic language agent framework
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
 ┃   ┣ 📂agents # Package for the "agents" of sr-OLTHAD
 ┃   ┃ ┣ 📂attempt_summarizer
 ┃   ┃ ┣ 📂backtracker
 ┃   ┃ ┣ 📂forgetter
 ┃   ┃ ┣ 📂planner
 ┃   ┣ ...
 ┃   ┣ 📜sr_olthad.py # Main importable sr-OLTHAD class
 ┃   ┣ 📜olthad.py # Everything OLTHAD-related: OlthadTraversal, TaskNode, etc.
 ┃   ┗ 📜utils.py
 ┃
 ┣ 📜quick_tests.py # Ad-hoc testing scripts
 ┣ 📜run_gui.py
 ┗ 📜requirements.txt
```
