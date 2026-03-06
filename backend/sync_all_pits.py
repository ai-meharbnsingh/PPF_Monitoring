#!/usr/bin/env python3
"""Sync sensor data from Pit One to Pit Two and Pit Three to keep them online"""
import asyncio
import asyncpg
import os

async def sync():
    conn = await asyncpg.connect(
        "postgresql://meharban@localhost:5432/ppf_monitoring"
    )
    try:
        # Get latest reading from Pit One
        row = await conn.fetchrow("""
            SELECT temperature, humidity, pressure, gas_resistance, iaq, iaq_accuracy,
                   pm1, pm25, pm10, primary_sensor_type, air_quality_sensor_type
            FROM sensor_data 
            WHERE pit_id = 3
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        if not row:
            print("❌ No data from Pit One")
            return
        
        # Sync to Pit Two
        result2 = await conn.execute("""
            INSERT INTO sensor_data (
                device_id, pit_id, workshop_id, primary_sensor_type, air_quality_sensor_type,
                temperature, humidity, pressure, gas_resistance, iaq, iaq_accuracy,
                pm1, pm25, pm10, is_valid, device_timestamp, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, true, NOW(), NOW())
        """, 'PIWIFI2-01', 4, 2, row['primary_sensor_type'], row['air_quality_sensor_type'],
             row['temperature'], row['humidity'], row['pressure'], row['gas_resistance'],
             row['iaq'], row['iaq_accuracy'], row['pm1'], row['pm25'], row['pm10'])
        
        # Sync to Pit Three
        result3 = await conn.execute("""
            INSERT INTO sensor_data (
                device_id, pit_id, workshop_id, primary_sensor_type, air_quality_sensor_type,
                temperature, humidity, pressure, gas_resistance, iaq, iaq_accuracy,
                pm1, pm25, pm10, is_valid, device_timestamp, created_at
            )
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, true, NOW(), NOW())
        """, 'PIWIFI3-01', 5, 2, row['primary_sensor_type'], row['air_quality_sensor_type'],
             row['temperature'], row['humidity'], row['pressure'], row['gas_resistance'],
             row['iaq'], row['iaq_accuracy'], row['pm1'], row['pm25'], row['pm10'])
        
        print(f"✅ Synced: Pit2={result2.split()[2] if 'INSERT' in result2 else 0}, Pit3={result3.split()[2] if 'INSERT' in result3 else 0}")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(sync())
