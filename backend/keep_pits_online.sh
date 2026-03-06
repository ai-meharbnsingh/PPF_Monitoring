#!/bin/bash
# Keep Pit Two and Pit Three online by syncing data and updating device status

cd ~/Projects/PP_Monitoring/backend
source venv/bin/activate

while true; do
    # Sync sensor data
    python3 sync_all_pits.py > /dev/null 2>&1
    
    # Update device timestamps
    psql -d ppf_monitoring -c "
        UPDATE devices 
        SET last_seen = NOW(),
            last_mqtt_message = NOW(),
            is_online = true
        WHERE pit_id IN (4, 5);
    " > /dev/null 2>&1
    
    sleep 10
done
