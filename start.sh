#!/bin/bash

# NOTE: This script is invoked by the Dockerfile and is responsible for starting the Minecraft server and running the sr-OLTHAD + SemanticSteve + GUI script.

set -e  # Exit on any error

# Check if running interactively
if [ ! -t 0 ]; then
    if [ -z "$EULA" ] || [ -z "$MC_USERNAME" ] || [ -z "$MC_PASSWORD" ]; then
        echo "Error: EULA and MC_USERNAME, must be set via environment variables in non-interactive mode."
        echo "Example: docker run -e EULA=TRUE -e MC_USERNAME=microsoftaccountemail@example.com ..."
        exit 1
    fi
fi

# Handle EULA agreement
if [ -z "$EULA" ]; then
    echo "Do you agree to the Minecraft EULA? (See https://www.minecraft.net/en-us/eula)"
    while true; do
        read -p "Enter 'yes' or 'no': " EULA
        case "$EULA" in
            [Yy][Ee][Ss])
                export EULA=TRUE
                break
                ;;
            [Nn][Oo])
                echo "Error: You must agree to the Minecraft EULA to run the server."
                exit 1
                ;;
            *)
                echo "Invalid input. Please enter 'yes' or 'no'."
                ;;
        esac
    done
else
    if [ "$EULA" != "TRUE" ]; then
        echo "Error: EULA must be set to 'TRUE' to accept the Minecraft EULA."
        exit 1
    fi
fi

# Check if MC_USERNAME is set, otherwise prompt for it
if [ -z "$MC_USERNAME" ]; then
    read -p "Enter Minecraft username: " MC_USERNAME
    if [ -z "$MC_USERNAME" ]; then
        echo "Error: Username cannot be empty."
        exit 1
    fi
    export MC_USERNAME
fi

# Start Minecraft server in background
echo "Starting Minecraft server..."
/start &
MC_PID=$!

# Wait for Minecraft port (25565) to become available
echo "Waiting for Minecraft to initialize..."
timeout 60 bash -c 'until nc -z localhost 25565; do sleep 2; done' || {
    echo "Error: Minecraft server failed to start within 60 seconds."
    kill $MC_PID
    exit 1
}

echo "Minecraft server is running. Running 'run_gui_semantic_steve.py'..."
/usr/local/bin/uv run --python 3.11 python3.11 /app/research/scripts/run_gui_semantic_steve.py

# Keep container alive
wait $MC_PID
