#!/usr/bin/env sh

set -e
cd "$(dirname "$0")"  # always run from the script's directory

# Make sure uv is installed
if ! command -v uv ; then
    echo "please install uv: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi
# Install dependencies into a virtual environment
uv sync --all-extras

# Make sure git pre-commit hooks are set up
if ! command -v pre-commit ; then
    uv tool install pre-commit
fi
pre-commit install

# Create a .env file
if [ ! -f .env ] && [ ! -d .env ] ; then
    {
        echo "OPENAI_API_KEY=your-api-key-goes-here"
    } >> .env
fi
