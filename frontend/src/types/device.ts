import type { DeviceCommand, DeviceStatus, SensorTypeCode } from './common'

// ─── Device response ──────────────────────────────────────────────────────────
export interface DeviceResponse {
  device_id: string
  workshop_id: number
  pit_id: number | null
  pit_name: string | null
  primary_sensor_type_code: SensorTypeCode | null
  air_quality_sensor_type_code: SensorTypeCode | null
  report_interval_seconds: number
  status: DeviceStatus
  firmware_version: string | null
  mac_address: string | null
  ip_address: string | null
  is_online: boolean
  last_seen: string | null
  license_key: string | null
  created_at: string
  updated_at: string | null
}

// ─── Device register request ──────────────────────────────────────────────────
export interface DeviceRegisterRequest {
  device_id: string
  pit_id: number
  primary_sensor_type_code: SensorTypeCode
  air_quality_sensor_type_code?: SensorTypeCode | null
  report_interval_seconds?: number
  mac_address?: string
  firmware_version?: string
}

// ─── Device register response ─────────────────────────────────────────────────
export interface DeviceRegisterResponse {
  device_id: string
  license_key: string
  mqtt_topic: string
  command_topic: string
  firmware_config: {
    mqtt_broker: string
    mqtt_port: number
    workshop_id: string
    pit_id: string
    device_id: string
    license_key: string
  }
}

// ─── Command request ──────────────────────────────────────────────────────────
export interface DeviceCommandRequest {
  command: DeviceCommand
  reason?: string
  payload?: Record<string, unknown>
}

// ─── Command response ─────────────────────────────────────────────────────────
export interface DeviceCommandResponse {
  command_id: number
  device_id: string
  command: DeviceCommand
  status: string
  issued_at: string
}
