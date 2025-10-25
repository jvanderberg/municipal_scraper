#!/bin/bash
# Setup script for Municipal Website Scraper
# Creates virtual environment and installs dependencies

set -e  # Exit on error

echo "=========================================="
echo "Municipal Website Scraper - Setup"
echo "=========================================="
echo

# Check if Python 3 is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed or not in PATH"
    exit 1
fi

echo "✓ Python 3 found: $(python3 --version)"
echo

# Create virtual environment
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
    read -p "Do you want to recreate it? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf venv
    else
        echo "Keeping existing virtual environment"
    fi
fi

if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi

echo

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip > /dev/null 2>&1

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

echo
echo "=========================================="
echo "✓ Setup complete!"
echo "=========================================="
echo
echo "Next steps:"
echo "  1. Run the scraper with: ./run.sh <url>"
echo "  2. Example: ./run.sh https://www.cityofexample.gov"
echo
