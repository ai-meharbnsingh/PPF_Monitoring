import type { SensorStatus } from '@/types/common'

// ─── Sensor display units ─────────────────────────────────────────────────────

export const SENSOR_UNITS: Record<string, string> = {
  temperature: '°C',
  humidity: '%',
  pm25: 'μg/m³',
  pm10: 'μg/m³',
  pm1: 'μg/m³',
  iaq: 'IAQ',
  pressure: 'hPa',
  gas_resistance: 'kOhm',
}

export const SENSOR_LABELS: Record<string, string> = {
  temperature: 'Temperature',
  humidity: 'Humidity',
  pm25: 'PM2.5',
  pm10: 'PM10',
  pm1: 'PM1',
  iaq: 'Air Quality',
  pressure: 'Pressure',
  gas_resistance: 'Gas Resistance',
}

// ─── Status display labels ────────────────────────────────────────────────────

export const STATUS_LABELS: Record<SensorStatus, string> = {
  good: 'Good',
  warning: 'Warning',
  critical: 'Critical',
  unknown: 'Unknown',
}

// ─── Local storage keys ───────────────────────────────────────────────────────

export const LS_TOKEN_KEY = 'ppf_token'
export const LS_USER_KEY = 'ppf_user'
