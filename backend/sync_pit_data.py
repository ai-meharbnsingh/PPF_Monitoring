#!/usr/bin/env python3
"""
Sync sensor data from Pit One (id=3) to Pit Two (id=4)
Run this periodically to keep demo pit data fresh
"""

import asyncio
import asyncpg
import os

async def sync_sensor_data():
    # Get DB URL from environment or use default
    db_url = os.getenv(
        "DATABASE_URL", 
        "postgresql://meharban@localhost:5432/ppf_monitoring"
    )
    
    conn = await asyncpg.connect(db_url)
    
    try:
        # Copy recent sensor data from Pit One to Pit Two
        # Only copy data from last 5 minutes that hasn't been copied yet
        result = await conn.execute("""
            INSERT INTO sensor_data (
                device_id, pit_id, workshop_id, primary_sensor_type, air_quality_sensor_type,
                temperature, humidity, pressure, gas_resistance, iaq, iaq_accuracy,
                pm1, pm25, pm10, particles_03um, particles_05um, particles_10um,
                particles_25um, particles_50um, particles_100um,
                is_valid, device_timestamp, created_at
            )
            SELECT 
                device_id, 
                4 AS pit_id,  -- Pit Two
                workshop_id, 
                primary_sensor_type, 
                air_quality_sensor_type,
                temperature, humidity, pressure, gas_resistance, iaq, iaq_accuracy,
                pm1, pm25, pm10, particles_03um, particles_05um, particles_10um,
                particles_25um, particles_50um, particles_100um,
                is_valid, device_timestamp, created_at
            FROM sensor_data 
            WHERE pit_id = 3
              AND created_at > NOW() - INTERVAL '2 minutes'
              AND NOT EXISTS (
                  SELECT 1 FROM sensor_data s2 
                  WHERE s2.pit_id = 4 
                    AND s2.device_timestamp = sensor_data.device_timestamp
              )
            ORDER BY created_at DESC
        """)
        
        # asyncpg returns "INSERT 0 0" format
        if "INSERT" in result:
            count = int(result.split()[2]) if len(result.split()) > 2 else 0
            if count > 0:
                print(f"✅ Synced {count} new readings to Pit Two")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(sync_sensor_data())
