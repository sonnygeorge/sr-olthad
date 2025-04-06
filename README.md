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

## Contributing

This project uses the following tooling:
- [uv](https://docs.astral.sh/uv/) for dependency/version management
- [ruff](https://docs.astral.sh/ruff/) for linting and formatting

### Quick Start

1. Make sure you have `uv` installed (official installation instructions [here](https://docs.astral.sh/uv/getting-started/installation/))
2. Run `./setup.sh`
3. Make sure you have environment variable `OPENAI_API_KEY` set
    - The setup script creates a `.env` file for you where you can put your API key
    - You can also use any normal method for setting environment variables, such as `export OPENAI_API_KEY={your key}`
4. Run the GUI with `uv run run_gui.py`

### Repo Structure

```python
📦sr-olthad
 ┣ 📂sr-olthad # Generalized package that could be published to PyPI
 ┃ ┗ 📂src
 ┃   ┗ 📂sr_olthad # Package for sr-OLTHAD
 ┃     ┣ 📂agents # Package for the "agents" of sr-OLTHAD
 ┃     ┃ ┣ 📜attempt_summarizer.py
 ┃     ┃ ┣ 📜backtracker.py
 ┃     ┃ ┣ 📜forgetter.py
 ┃     ┃ ┗ 📜planner.py
 ┃     ┣ 📂common
 ┃     ┃ ┣ 📂agents
 ┃     ┃ ┃ ┗ 📜instruct_lm.py
 ┃     ┃ ┣ 📜lms.py
 ┃     ┃ ┣ 📜schema.py
 ┃     ┃ ┗ 📜utils.py
 ┃     ┣ ...
 ┃     ┣ 📜olthad.py # Everything OLTHAD-related: OlthadTraversal, TaskNode, etc.
 ┃     ┣ 📜sr_olthad.py # Main importable sr-OLTHAD class
 ┃     ┗ 📜utils.py
 ┃
 ┃ # Can hypothetically include other packages for other methods, such as:
 ┣ 📂react # Code pertaining to the recreation of ReAct prompting
 ┃
 ┣ 📂src # Code specifically to apply sr-OLTHAD to Minecraft
 ┃ ┗ 📂sr_olthad_minecraft
 ┃   ┗ 📂gui
 ┃
 ┣ 📜pyproject.toml # Project setup
 ┣ 📜quick_tests.py # Ad-hoc testing scripts
 ┗ 📜run_gui.py
```
