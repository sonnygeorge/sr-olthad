<!--
TODO: Wrap lines in LM `TextBox`s?
TODO: Internal "notepad"
-->

# sr-OLTHAD

<div align="left">
	<img src="https://img.shields.io/badge/status-under%20development-orange"/></a>
    <a href="https://github.com/psf/black"><img src="https://img.shields.io/badge/code_style-black-000000.svg"/></a>
</div>

**S**tructured **R**easoning With **O**pen-**L**anguage **H**ierarchies of **A**ny **D**epth

Think the project is interesting? Give it a star! ⭐

### Quick Start

This project uses the following tooling:

- [uv](https://docs.astral.sh/uv/) for dependency/version management
- [ruff](https://docs.astral.sh/ruff/) for linting and formatting

1. Make sure you have `uv` installed (official installation instructions [here](https://docs.astral.sh/uv/getting-started/installation/))
2. Run `./setup.sh`
3. Make sure you have environment variable `OPENAI_API_KEY` set
   - The `setup.sh` script creates a `.env` file for you where you can put your API key
   - You can also use any normal method for setting environment variables, such as `export OPENAI_API_KEY={your key}`
4. Finally, to run sr-OLTHAD with SemanticSteve and visualize outputs in the GUI, you have to install SemanticSteve with this (temporarily manual) process:

   1. Make sure you `node` and `yarn` installed
   2. Install SemanticSteve from the most actualized branch: `uv pip install git+https://github.com/sonnygeorge/semantic-steve.git@gen/refactor`
   3. Manually install its new requirements: `uv pip install prompt_toolkit pyzmq`
   4. Manually install the `semantic-steve` JS dependencies:
      - `cd .venv/lib/python3.11/site-packages/semantic_steve/js`
      - `yarn install`

Now you should be able to run sr-OLTHAD with SemanticSteve and visualize outputs in the GUI with `uv run research/scripts/run_gui_semantic_steve.py`.

### Repo Structure

```python
📦
 ┃ 📦 sr-olthad # Standalone sr-OLTHAD package that could be published to PyPI
 ┃  ┣ 📂 sr_olthad # sr-OLTHAD source code
 ┃  ┗ ...
 ┣ 📂 research # Code/data for research tasks
 ┃  ┣ 📂 data
 ┃  ┣ 📂 experiments
 ┃  ┣ 📂 eval_harness
 ┃  ┗ 📂 scripts
 ┣ 📜pyproject.toml
 ┗ 📜uv.lock
```
