# SARG (Stochastic Adversarial Reasoning Game) - Development Environment
# Python 3.11 with RL and Scientific Computing Stack

FROM python:3.11-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /workspace

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    git \
    curl \
    wget \
    vim \
    htop \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip setuptools wheel && \
    pip install -r requirements.txt

# Create necessary directories
RUN mkdir -p /workspace/data/games \
             /workspace/data/logs \
             /workspace/data/models \
             /workspace/configs \
             /workspace/notebooks

# Set Python path
ENV PYTHONPATH=/workspace/src:$PYTHONPATH

# Default command
CMD ["/bin/bash"]
