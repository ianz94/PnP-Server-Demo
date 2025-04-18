#!/bin/bash

# Check Python version
REQUIRED_PYTHON_VERSION="3.8"
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')

if [[ $(echo "$PYTHON_VERSION < $REQUIRED_PYTHON_VERSION" | bc -l) -eq 1 ]]; then
    echo "Error: Python $REQUIRED_PYTHON_VERSION or higher is required (found $PYTHON_VERSION)"
    exit 1
fi

echo "Creating virtual environment with Python $PYTHON_VERSION..."
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip3 install -r requirements.txt

echo ""
echo "Setup complete! Use 'source venv/bin/activate' to activate the virtual environment."