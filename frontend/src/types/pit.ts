import type { PitStatus } from './common'

// ─── Embedded device summary inside pit response ──────────────────────────────
export interface DeviceSummaryInPit {
  device_id: string
  is_online: boolean
  last_seen: string | null
  primary_sensor_type_code: string | null
  air_quality_sensor_type_code: string | null
}

// ─── Pit list item ────────────────────────────────────────────────────────────
export interface PitSummary {
  id: number
  workshop_id: number
  pit_number: number
  name: string
  status: PitStatus
  camera_ip: string | null
  camera_model: string | null
  camera_rtsp_path: string | null
  camera_is_online: boolean
  camera_last_seen: string | null
  device: DeviceSummaryInPit | null
  created_at: string
  updated_at: string | null
}

// ─── Full pit response ────────────────────────────────────────────────────────
export interface PitResponse extends PitSummary {
  report_interval_seconds: number | null
}
