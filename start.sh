#!/bin/bash
set -e  # Exit on any error

# Start Minecraft server in background
/start &
MC_PID=$!

# Wait for Minecraft port (25565) to become available
echo "Waiting for Minecraft to initialize..."
timeout 60 bash -c 'until nc -z localhost 25565; do sleep 2; done' || {
  echo "Minecraft failed to start within 60s"
  exit 1
}

echo "Minecraft server is running. Running `run_gui_semantic_steve.py`..."
/usr/local/bin/uv run --python 3.11 python3.11 /app/research/scripts/run_gui_semantic_steve.py

# Keep container alive
wait $MC_PID
