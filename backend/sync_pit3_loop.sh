#!/bin/bash
# Continuous sync from Pit One to Pit Three
cd ~/Projects/PP_Monitoring/backend
source venv/bin/activate
while true; do
    python3 sync_pit3_data.py > /dev/null 2>&1
    sleep 30
done
