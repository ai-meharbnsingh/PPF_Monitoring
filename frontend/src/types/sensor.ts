import type { SensorStatus, SensorTypeCode } from './common'

// ─── Latest sensor summary (one per pit) — matches backend LatestSensorSummary
export interface LatestSensorSummary {
  pit_id: number
  device_id: string | null
  is_device_online: boolean
  // Readings (nullable — depends on sensor type fitted)
  temperature: number | null     // °C
  humidity: number | null        // %RH
  pm1: number | null             // μg/m³
  pm25: number | null            // μg/m³
  pm10: number | null            // μg/m³
  pressure: number | null        // hPa (BME680)
  iaq: number | null             // IAQ index 0–500 (BME680)
  // Status labels from backend threshold evaluation
  temp_status: SensorStatus
  humidity_status: SensorStatus
  pm25_status: SensorStatus
  pm10_status: SensorStatus
  iaq_status: SensorStatus
  last_reading_at: string | null
}

// ─── Full sensor reading row (history) ───────────────────────────────────────
export interface SensorReadingResponse {
  id: number
  device_id: string
  pit_id: number
  workshop_id: number
  primary_sensor_type: SensorTypeCode | null
  air_quality_sensor_type: SensorTypeCode | null
  temperature: number | null
  humidity: number | null
  pressure: number | null
  gas_resistance: number | null
  iaq: number | null
  iaq_accuracy: number | null
  pm1: number | null
  pm25: number | null
  pm10: number | null
  particles_03um: number | null
  particles_05um: number | null
  particles_10um: number | null
  particles_25um: number | null
  particles_50um: number | null
  particles_100um: number | null
  is_valid: boolean
  validation_notes: string | null
  device_timestamp: string
  created_at: string
}

// ─── Aggregate stats ──────────────────────────────────────────────────────────
export interface SensorStatsResponse {
  pit_id: number
  device_id: string | null
  period_start: string
  period_end: string
  reading_count: number
  temp_avg: number | null
  temp_min: number | null
  temp_max: number | null
  humidity_avg: number | null
  humidity_min: number | null
  humidity_max: number | null
  pm25_avg: number | null
  pm25_max: number | null
  pm10_avg: number | null
  pm10_max: number | null
  iaq_avg: number | null
  iaq_max: number | null
}

// ─── WebSocket sensor_update event data shape ─────────────────────────────────
export interface WsSensorUpdateData {
  temperature: number | null
  humidity: number | null
  pm1: number | null
  pm25: number | null
  pm10: number | null
  iaq: number | null
  pressure: number | null
  is_online: boolean
  recorded_at: string
}
