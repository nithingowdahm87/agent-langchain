#!/bin/bash

# Navigate to the script's directory (devops-agent root)
SCRIPT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
cd "$SCRIPT_DIR"

# Source the Virtual Environment
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
else
    echo "⚠️  Virtual environment 'venv' not found. Please run 'python3 -m venv venv' and install requirements."
fi

# Source Environment Variables
if [ -f ".env" ]; then
    source .env
else
    echo "⚠️  '.env' file not found. System will run in Mock Mode. Copy '.env.example' to '.env' to configure keys."
fi

# Run the Agent
python3 main.py "$@"
