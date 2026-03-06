#!/usr/bin/env python3
"""Sync sensor data from Pit One to Pit Three"""
import asyncio
import asyncpg
import os

async def sync():
    conn = await asyncpg.connect(
        "postgresql://meharban@localhost:5432/ppf_monitoring"
    )
    try:
        result = await conn.execute("""
            INSERT INTO sensor_data (
                device_id, pit_id, workshop_id, primary_sensor_type, air_quality_sensor_type,
                temperature, humidity, pressure, gas_resistance, iaq, iaq_accuracy,
                pm1, pm25, pm10, particles_03um, particles_05um, particles_10um,
                particles_25um, particles_50um, particles_100um,
                is_valid, device_timestamp, created_at
            )
            SELECT 
                'PIWIFI3-01', 5, workshop_id, primary_sensor_type, air_quality_sensor_type,
                temperature, humidity, pressure, gas_resistance, iaq, iaq_accuracy,
                pm1, pm25, pm10, particles_03um, particles_05um, particles_10um,
                particles_25um, particles_50um, particles_100um,
                is_valid, device_timestamp, NOW()
            FROM sensor_data 
            WHERE pit_id = 3
              AND created_at > NOW() - INTERVAL '2 minutes'
              AND NOT EXISTS (
                  SELECT 1 FROM sensor_data s2 
                  WHERE s2.pit_id = 5 AND s2.device_timestamp = sensor_data.device_timestamp
              )
            ON CONFLICT DO NOTHING
        """)
        if "INSERT" in result:
            count = int(result.split()[2]) if len(result.split()) > 2 else 0
            if count > 0:
                print(f"✅ Synced {count} readings to Pit Three")
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(sync())
