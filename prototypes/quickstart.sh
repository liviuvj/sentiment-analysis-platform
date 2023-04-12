#!/bin/bash

# Version 1.0
#
# Quickstart script for the project's prototype.

# Activate environment
source ../.venv/bin/activate

# Clone repository and run platform
cd extraction
git clone --depth 1 https://github.com/airbytehq/airbyte.git
cd airbyte
./run-ab-platform.sh

# Run MongoDB instance
cd ../../mongodb
docker compose up -d

# Configure data extraction and data loading pipeline
cd ../extraction
python config.py
