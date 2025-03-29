#!/usr/bin/env sh

set -e
cd "$(dirname "$0")"  # always run from the script's directory

# make sure uv is installed
if ! command -v uv ; then
    echo "please install uv: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi
# install dependencies into a virtual environment
uv sync --all-extras

# make sure git pre-commit hooks are set up
if ! command -v pre-commit ; then
    uv tool install pre-commit
fi
pre-commit install

# create a .env file
if [ ! -f .env ] && [ ! -d .env ] ; then
    {
        echo "OPENAI_API_KEY=your-api-key-goes-here"
    } >> .env
fi
