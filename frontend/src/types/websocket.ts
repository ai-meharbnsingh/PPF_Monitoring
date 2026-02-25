import type { AlertSeverity, AlertType, JobStatus } from './common'

// ─── All WebSocket server→client event shapes ─────────────────────────────────

export interface WsSensorUpdateEvent {
  event: 'sensor_update'
  pit_id: number
  data: {
    temperature: number | null
    humidity: number | null
    pm1: number | null
    pm25: number | null
    pm10: number | null
    iaq: number | null
    pressure: number | null
    gas_resistance: number | null
    is_online: boolean
    recorded_at: string
  }
}

export interface WsJobStatusEvent {
  event: 'job_status'
  job_id: number
  pit_id: number
  data: {
    previous_status: JobStatus | null
    new_status: JobStatus
    time_remaining_minutes: number | null
    updated_at: string
  }
}

export interface WsAlertEvent {
  event: 'alert'
  pit_id: number | null
  data: {
    alert_id: number
    alert_type: AlertType
    severity: AlertSeverity
    message: string
    trigger_value: number | null
    threshold_value: number | null
  }
}

export interface WsDeviceOfflineEvent {
  event: 'device_offline'
  pit_id: number
  data: {
    device_id: string
    last_seen: string | null
  }
}

export interface WsDeviceOnlineEvent {
  event: 'device_online'
  pit_id: number
  data: {
    device_id: string
  }
}

export interface WsCameraOfflineEvent {
  event: 'camera_offline'
  pit_id: number
  data: Record<string, unknown>
}

export interface WsPongEvent {
  event: 'pong'
  timestamp: string
}

export interface WsErrorEvent {
  event: 'error'
  message: string
}

export interface WsSubscribedEvent {
  event: 'subscribed'
  workshop_id?: number
  pit_id?: number
}

// Union type of all server→client events
export type WsServerEvent =
  | WsSensorUpdateEvent
  | WsJobStatusEvent
  | WsAlertEvent
  | WsDeviceOfflineEvent
  | WsDeviceOnlineEvent
  | WsCameraOfflineEvent
  | WsPongEvent
  | WsErrorEvent
  | WsSubscribedEvent

// Client→server actions
export interface WsSubscribePitAction {
  action: 'subscribe_pit'
  pit_id: number
}

export interface WsSubscribeWorkshopAction {
  action: 'subscribe_workshop'
  workshop_id: number
}

export interface WsUnsubscribeAction {
  action: 'unsubscribe'
  pit_id: number
}

export interface WsPingAction {
  action: 'ping'
}

export type WsClientAction =
  | WsSubscribePitAction
  | WsSubscribeWorkshopAction
  | WsUnsubscribeAction
  | WsPingAction
