#!/bin/bash
# Keep all pits online with fresh sensor data
cd ~/Projects/PP_Monitoring/backend
source venv/bin/activate
while true; do
    python3 sync_all_pits.py > /dev/null 2>&1
    sleep 20
done
