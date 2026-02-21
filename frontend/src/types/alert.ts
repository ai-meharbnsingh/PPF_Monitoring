import type { AlertSeverity, AlertType } from './common'

// ─── Alert response ───────────────────────────────────────────────────────────
export interface AlertResponse {
  id: number
  workshop_id: number
  pit_id: number | null
  device_id: string | null
  alert_type: AlertType
  severity: AlertSeverity
  message: string
  trigger_value: number | null
  threshold_value: number | null
  is_acknowledged: boolean
  acknowledged_by_user_id: number | null
  acknowledged_at: string | null
  resolved_at: string | null
  sms_sent: boolean
  email_sent: boolean
  created_at: string
}

// ─── Alert config (thresholds) ────────────────────────────────────────────────
export interface AlertConfigResponse {
  id: number
  workshop_id: number
  temp_min: number
  temp_max: number
  humidity_max: number
  pm25_warning: number
  pm25_critical: number
  pm10_warning: number
  pm10_critical: number
  iaq_warning: number
  iaq_critical: number
  device_offline_threshold_seconds: number
  camera_offline_threshold_seconds: number
  notify_via_sms: boolean
  notify_via_email: boolean
  notify_via_webhook: boolean
  webhook_url: string | null
  created_at: string
  updated_at: string | null
}

// ─── Alert config update request ─────────────────────────────────────────────
export interface AlertConfigUpdate {
  temp_min?: number
  temp_max?: number
  humidity_max?: number
  pm25_warning?: number
  pm25_critical?: number
  pm10_warning?: number
  pm10_critical?: number
  iaq_warning?: number
  iaq_critical?: number
  device_offline_threshold_seconds?: number
  camera_offline_threshold_seconds?: number
  notify_via_sms?: boolean
  notify_via_email?: boolean
  notify_via_webhook?: boolean
  webhook_url?: string | null
}

// ─── Acknowledge request ──────────────────────────────────────────────────────
export interface AlertAcknowledgeRequest {
  notes?: string
}

// ─── WebSocket alert event data ───────────────────────────────────────────────
export interface WsAlertData {
  alert_id: number
  alert_type: AlertType
  severity: AlertSeverity
  message: string
  trigger_value: number | null
  threshold_value: number | null
}
