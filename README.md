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

## 📒 ℹ️ How to run sr-OLTHAD + GUI w/ [SemanticSteve](https://github.com/sonnygeorge/semantic-steve)

### 📒 🐋 Using Docker (recommended)

---

(Make sure you have Docker installed)

#### 1️⃣ Build the Docker image:

- ❗ **IMPORTANT:** ~1-4 GBs of disk space is required for the image.

```bash
docker build -t sr-olthad-ss-gui .
```

⚠️ (this takes a while, ~1.5-8 minutes)

#### 2️⃣ Run the Docker container:

- ❗ **IMPORTANT:** You **MUST** use `-it` so that you can enter 'yes' to agree to the Minecraft EULA.
- ❗ **IMPORTANT:** You need to link the ports you want to use, e.g.:
  - `25565` for the Minecraft server
  - `3000` for to view the bot's POV
  - `8080` for the sr-OLTHAD GUI
- ❗ **IMPORTANT:** You need to set whatever environment variables you need, e.g.,
  - `OPENAI_API_KEY`
  - `GROQ_API_KEY`
  - etc.

  ℹ️ See `sr-olthad/sr_olthad/config.py` to know what API's are configured for use.
- ❗ **IMPORTANT:** Replace the `MC_USERNAME` with your Microsoft account email address.

```bash
docker run -it \
-p 25565:25565 \
-p 3000:3000 \
-p 8080:8080 \
-e OPENAI_API_KEY="$OPENAI_API_KEY" \
-e GROQ_API_KEY="$GROQ_API_KEY" \
-e MC_USERNAME="microsoftaccountemail@example.com" \
-e HIGHEST_LEVEL_TASK="Acquire iron." \
sr-olthad-ss-gui
```

⚠️ (this takes a while)

#### 3️⃣ Log in with Microsoft:

Eventually, you will see a message like this in the terminal:

```text
To sign in, use a web browser to open the page https://www.microsoft.com/link and use the code 3ABE9FVH or visit http://microsoft.com/link?otc=3ABE9FVH
```

Follow this link and do the Microsoft login flow.

#### 4️⃣ Open the GUI and Bot POV:

- Open the GUI at `localhost:8080`
- Open the bot POV at `localhost:3000`

(Assuming these were the ports you linked in the `docker run` command)

#### 🏁 Voila!

🥳 You are now running sr-OLTHAD with SemanticSteve and the GUI!

#### ❗😎 Pro Tip ❗

Since every re-run requires (1) logging in to Microsoft and (2) waiting for the server to start, invoking `docker run` every time you want to run the `run_gui_semantic_steve.py` script is a _major_ hassle!

Instead, we recommend leveraging the in-container terminal accessible via [Docker Desktop](https://www.docker.com/products/docker-desktop/) to re-run the script.

![image-of-how-to-open](https://i.imgur.com/4lMADEk.png)

Here are some useful commands (assumes `pwd` is `/app`, which it should be by default):
- `pkill -2 python`
  - Sends SIGINT to any running Python processes (stopping any previously running script)
- `export HIGHEST_LEVEL_TASK="Acquire diamond."`
  - Re-sets sr-OLTHAD's highest-level task.
- `uv run research/scripts/run_gui_semantic_steve.py`
  - Re-runs the script.

![image-of-running-commands](https://i.imgur.com/CesE0vR.png)


---

### 📒 🚫🐋 **_Not_** Using Docker (_not_ recommended)

---

#### 1️⃣ Install Python requirements into a virtual environment w/ `uv`:

```bash
uv sync
```

(Learn how to install `uv` [here](https://docs.astral.sh/uv/#installation))

#### 2️⃣ Install/verify Node.js 22:

You must have Node.js 22 installed. You can check your version with:

```bash
node --version
```

If the result is not `v22.x.x`, you **MUST** install and link Node.js 22. We recommend using [nvm](https://github.com/nvm-sh/nvm) (Node Version Manager) for managing this.

#### 3️⃣ Install/verify `yarn`:

- You must have `yarn` installed. Learn how to install it [here](https://classic.yarnpkg.com/docs/install/).

#### 4️⃣ Load a survival-mode (peaceful) single-player world locally:

(Use the [Minecraft launcher](https://www.minecraft.net/en-us/download?tabs=%7B%22MCEXP_TabsB%22%3A0%7D) w/ your Microsoft Account)

- **IMPORTANT:** The world MUST be ❗ **_Java Edition, version 1.21.1_** ❗
    - _DO NOT_ use 1.21.5 (the latest release)!

#### 5️⃣ Open this world to LAN on port `25565`:

In Minecraft, press the Esc key, and click Open to LAN.

#### 6️⃣ Make sure you have this project directory as your `PYTHONPATH` env variable:

You can set this by running:

```bash
export PYTHONPATH=$(pwd)
```

You can verify this by running:

```bash
echo $PYTHONPATH
```

#### 7️⃣ Set up your `.env` to have the necessary LLM API keys (or export them as env variables)

For whatever API's sr-OLTHAD is currently configured to use (see `sr-olthad/sr_olthad/config.py`), you will need API keys.

These need to be environment variables at run time. To accomplish this, you can either:
1. Create a `.env` file with their declaration (python will load them at run time), e.g.:

```
OPENAI_API_KEY="..."
GROQ_API_KEY="..."
...
```
2. ...or export them to your terminal session manually, e.g.:

```bash
export OPENAI_API_KEY="..."
export GROQ_API_KEY="..."
...
```

#### 8️⃣ Run the script:

```bash
uv run research/scripts/run_gui_semantic_steve.py
```

#### 9️⃣ Open the GUI and Bot POV:

- Open the GUI at `localhost:8080`
- Open the bot POV at `localhost:3000`

#### 🏁 Voila!

🥳 You are now running sr-OLTHAD with SemanticSteve and the GUI!
