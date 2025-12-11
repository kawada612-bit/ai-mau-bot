#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
cd "$SCRIPT_DIR"

# Activate virtual environment
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "⚠️  Virtual environment not found. Please run 'python3 -m venv venv' first."
    exit 1
fi

# Set environment to development
export MAU_ENV="development"

echo "🚀 Starting AI-Mau in DEVELOPMENT mode..."
echo "----------------------------------------"

# Run the bot
python -m src.app.main
