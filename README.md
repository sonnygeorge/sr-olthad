<!--
TODO: Move config as options passed to SrOlthad __init__?
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

### Contributing

This project uses the following tooling:

- [uv](https://docs.astral.sh/uv/) for dependency/version management
- [ruff](https://docs.astral.sh/ruff/) for linting and formatting

## How To Use

### ℹ️ Run sr-OLTHAD w/ Semantic Steve & GUI (w/out Docker)

#### 🚶 1. Install Python requirements into a virtual environment w/ `uv`:

```bash
uv sync
```

- Learn how to install `uv` [here](https://docs.astral.sh/uv/#installation).

#### 🚶 2. Install/verify Node.js 22:

- You must have Node.js 22 installed. You can check your version with:

```bash
node --version
```

- If the result is not `v22.x.x`, you **MUST** install and link Node.js 22. We recommend using [nvm](https://github.com/nvm-sh/nvm) (Node Version Manager) to for this process.

#### 🚶 3. Install/verify `yarn`:

- You must have `yarn` installed. Learn how to install it [here](https://classic.yarnpkg.com/docs/install/).

#### 🚶 4. Load a survival-mode (peaceful) single-player world locally:

(Use the [Minecraft launcher](https://www.minecraft.net/en-us/download?tabs=%7B%22MCEXP_TabsB%22%3A0%7D) w/ your Microsoft Account)

#### 🚶 5. Open this world to LAN on port `25565`:

- In Minecraft, press the Esc key, and click Open to LAN.

#### 🚶 6. Run the script:

```bash
uv run research/scripts/run_gui_semantic_steve.py
```

#### 🚶 7. Open the GUI and Bot POV:

- Open the GUI at `localhost:8080`
- Open the bot POV at `localhost:3000`

#### 🏁 Voila!

You are now running sr-OLTHAD with SemanticSteve and the GUI!

### ℹ️ Run sr-OLTHAD w/ Semantic Steve & GUI (w/ Docker)

(Make sure you have Docker installed)

#### 🚶 1. Build the Docker image:

```bash
docker build -t sr-olthad-ss-gui .
```

⚠️ (this takes a while)

#### 🚶 2. Run the Docker container:

- ❗ **IMPORTANT:** You **MUST** use `-it` (the interactive terminal flag) so that you can enter 'yes' to agree to the Minecraft EULA.
- ❗ **IMPORTANT:** You need to link the ports you want to use (e.g., `25565` for the Minecraft server, `3000` for to view the bot's POV, and `8080` for the GUI)
- ❗ **IMPORTANT:** You need to set whatever environment variables you need (e.g., `OPENAI_API_KEY`, `GROQ_API_KEY`, etc.)
- ❗ **IMPORTANT:** Replace the `MC_USERNAME` with your Microsoft account email address.

```bash
docker run -it \
-p 25565:25565 \
-p 3000:3000 \
-p 8080:8080 \
-e OPENAI_API_KEY="$OPENAI_API_KEY" \
-e GROQ_API_KEY="$GROQ_API_KEY" \
-e MC_USERNAME="microsoftaccountemail@example.com" \
sr-olthad-ss-gui
```

⚠️ (this takes a while)

#### 🚶 3. Log in with Microsoft:

- After a number of minutes (getting the server up and running, installing `gl` at runtime, etc.), you should see a message in the terminal that says something like:

```text
To sign in, use a web browser to open the page https://www.microsoft.com/link and use the code 3ABE9FVH or visit http://microsoft.com/link?otc=3ABE9FVH
```

- You need to follow this link and do the Microsoft login flow.

#### 🚶 4. Open the GUI and Bot POV:

- Open the GUI at `localhost:8080`
- Open the bot POV at `localhost:3000`

(Assuming these were the ports you linked in the `docker run` command)

#### 🏁 Voila!

You are now running sr-OLTHAD with SemanticSteve and the GUI!
