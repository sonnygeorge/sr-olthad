FROM itzg/minecraft-server

# Install software-properties-common, curl, Node.js, and dependencies for canvas and gl
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    ca-certificates \
    gnupg \
    && \
    # Add Deadsnakes PPA for Python 3.11
    add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && apt-get install -y \
    netcat-openbsd \
    python3.11 \
    python3.11-venv \
    python3.11-distutils \
    pkg-config \
    build-essential \
    libcairo2-dev \
    libpango1.0-dev \
    libjpeg-dev \
    libpng-dev \
    libgif-dev \
    libxi-dev \
    libx11-dev \
    libxext-dev \
    libgl1-mesa-dev \
    libglx-dev \
    libegl1-mesa-dev \
    && \
    # Add NodeSource PPA for Node.js 22
    curl -fsSL https://deb.nodesource.com/gpgkey/nodesource-repo.gpg.key | gpg --dearmor -o /etc/apt/keyrings/nodesource.gpg && \
    echo "deb [signed-by=/etc/apt/keyrings/nodesource.gpg] https://deb.nodesource.com/node_22.x nodistro main" > /etc/apt/sources.list.d/nodesource.list && \
    apt-get update && \
    apt-get install -y nodejs && \
    # Install Yarn globally
    npm install -g yarn && \
    # Clean up apt cache
    rm -rf /var/lib/apt/lists/*

# Verify Node.js and Yarn versions
RUN node --version && yarn --version

# Install uv with specific location tracking
RUN curl -LsSf https://astral.sh/uv/install.sh | sh && \
    find / -name uv -type f 2>/dev/null | tee /uv_location.txt && \
    cat /uv_location.txt && \
    mkdir -p /usr/local/bin && \
    UV_PATH=$(cat /uv_location.txt | head -1) && \
    if [ -n "$UV_PATH" ]; then ln -s $UV_PATH /usr/local/bin/uv; fi

# Copy specific project files and directories
COPY sr-olthad /app/sr-olthad
COPY research /app/research
COPY pyproject.toml /app/pyproject.toml
COPY uv.lock /app/uv.lock

# Set the working directory
WORKDIR /app
ENV PYTHONPATH=/app

# Install Python dependencies using uv
RUN which uv || echo "uv not found in PATH" && \
    ls -la /usr/local/bin/ && \
    /usr/local/bin/uv sync --python 3.11

# Copy a wrapper script to control startup
COPY start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Set environment variables for Minecraft server
ENV VERSION=1.21.1
ENV DIFFICULTY=peaceful

# Use wrapper script as entrypoint
ENTRYPOINT ["/bin/bash", "/app/start.sh"]
