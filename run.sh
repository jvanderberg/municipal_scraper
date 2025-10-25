#!/bin/bash
# Run script for Municipal Website Scraper
# Activates virtual environment and runs the scraper

set -e  # Exit on error

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "Error: Virtual environment not found"
    echo "Please run ./setup.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Check if URL is provided
if [ $# -eq 0 ]; then
    echo "Usage: ./run.sh <base_url> [options]"
    echo
    echo "Examples:"
    echo "  ./run.sh https://www.cityofexample.gov"
    echo "  ./run.sh https://www.cityofexample.gov --max-depth 4"
    echo "  ./run.sh https://www.cityofexample.gov --delay 2.0 --output my_catalog"
    echo
    echo "Options:"
    echo "  --max-depth N    Maximum crawl depth (default: 3)"
    echo "  --delay N        Delay between requests in seconds (default: 1.0)"
    echo "  --output DIR     Output directory (default: output)"
    echo "  --user-agent STR Custom user agent string"
    echo
    exit 1
fi

# Run the scraper with all arguments
python main.py "$@"

echo
echo "Tip: Review the output directory before moving to LLM indexing phase"
