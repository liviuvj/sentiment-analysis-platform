#!/bin/bash

# Version 1.0
#
# Quickstart script for the project's prototype.

# Clone repository and run platform
cd extraction
git clone --depth 1 https://github.com/airbytehq/airbyte.git
cd airbyte
./run-ab-platform.sh

# Configure data extraction pipeline
cd ..
python config.py
