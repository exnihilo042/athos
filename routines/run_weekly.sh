#!/bin/bash
source /Users/clem/Sites/athos/.env
export ANTHROPIC_API_KEY
export DRIVE_PATH
/Users/clem/Sites/athos/venv/bin/python3 /Users/clem/Sites/athos/core/weekly_consolidator.py
