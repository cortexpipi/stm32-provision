#!/bin/bash


# Exit on error
set -e

# Create virtual environment if it doesn't exist
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
fi

# Avtivate virtual environment
source .venv/bin/activate

# Check if requirements file exists
if [ ! -f "utils/requirements.txt" ]; then
    echo "Requirements file not found"
    exit 1
fi

# Install dependencies if they are not installed
tmpfile=$(mktemp)
pip freeze > $tmpfile
diff $tmpfile utils/requirements.txt || pip install -r utils/requirements.txt
rm $tmpfile

# pip install -r utils/requirements.txt

# Run the tests
python3 -m unittest discover -s utils