#!/usr/bin/env python3
"""
Sync sensor data with 60-second lag between pits:
- Pit 1: Live (0s lag)
- Pit 2: 60 seconds behind Pit 1
- Pit 3: 120 seconds behind Pit 1 (60s behind Pit 2)
"""
import asyncio
import asyncpg
from datetime import datetime, timedelta, timezone

async def sync():
    conn = await asyncpg.connect(
        "postgresql://meharban@localhost:5432/ppf_monitoring"
    )
    try:
        # Get latest reading from Pit One (live)
        row = await conn.fetchrow("""
            SELECT temperature, humidity, pressure, gas_resistance, iaq, iaq_accuracy,
                   pm1, pm25, pm10, primary_sensor_type, air_quality_sensor_type,
                   created_at
            FROM sensor_data 
            WHERE pit_id = 3
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        if not row:
            print("❌ No data from Pit One")
            return
        
        now = datetime.now(timezone.utc)
        
        # Pit 2: 60 seconds old (1 minute behind)
        pit2_time = now - timedelta(seconds=60)
        result2 = await conn.execute("""
            INSERT INTO sensor_data (
                device_id, pit_id, workshop_id, primary_sensor_type, air_quality_sensor_type,
                temperature, humidity, pressure, gas_resistance, iaq, iaq_accuracy,
                pm1, pm25, pm10, is_valid, device_timestamp, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, true, $15, $15)
            ON CONFLICT DO NOTHING
        """, 'PIWIFI2-01', 4, 2, row['primary_sensor_type'], row['air_quality_sensor_type'],
             row['temperature'], row['humidity'], row['pressure'], row['gas_resistance'],
             row['iaq'], row['iaq_accuracy'], row['pm1'], row['pm25'], row['pm10'], pit2_time)
        
        # Pit 3: 120 seconds old (2 minutes behind)
        pit3_time = now - timedelta(seconds=120)
        result3 = await conn.execute("""
            INSERT INTO sensor_data (
                device_id, pit_id, workshop_id, primary_sensor_type, air_quality_sensor_type,
                temperature, humidity, pressure, gas_resistance, iaq, iaq_accuracy,
                pm1, pm25, pm10, is_valid, device_timestamp, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, true, $15, $15)
            ON CONFLICT DO NOTHING
        """, 'PIWIFI3-01', 5, 2, row['primary_sensor_type'], row['air_quality_sensor_type'],
             row['temperature'], row['humidity'], row['pressure'], row['gas_resistance'],
             row['iaq'], row['iaq_accuracy'], row['pm1'], row['pm25'], row['pm10'], pit3_time)
        
        # Update device timestamps to keep them online
        await conn.execute("""
            UPDATE devices 
            SET last_seen = NOW(),
                last_mqtt_message = NOW(),
                is_online = true
            WHERE pit_id IN (4, 5);
        """)
        
        print(f"✅ Pit1: LIVE | Pit2: -60s | Pit3: -120s")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(sync())
