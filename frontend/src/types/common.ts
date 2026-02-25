// ─── Enums (mirrors backend src/utils/constants.py) ──────────────────────────

export type UserRole = 'super_admin' | 'owner' | 'staff' | 'customer'

export type JobStatus =
  | 'waiting'
  | 'in_progress'
  | 'quality_check'
  | 'completed'
  | 'cancelled'

export type WorkType =
  | 'Full PPF'
  | 'Partial PPF'
  | 'Ceramic Coating'
  | 'Custom'

export type SensorStatus = 'good' | 'warning' | 'critical' | 'unknown'

export type AlertSeverity = 'info' | 'warning' | 'critical'

export type AlertType =
  | 'high_pm25'
  | 'high_pm10'
  | 'high_iaq'
  | 'temp_too_low'
  | 'temp_too_high'
  | 'humidity_too_high'
  | 'device_offline'
  | 'camera_offline'
  | 'license_invalid'
  | 'subscription_expiring'
  | 'subscription_suspended'

export type DeviceCommand =
  | 'DISABLE'
  | 'ENABLE'
  | 'RESTART'
  | 'UPDATE_FIRMWARE'
  | 'SET_INTERVAL'

export type DeviceStatus = 'active' | 'disabled' | 'suspended' | 'maintenance'

export type SensorTypeCode = 'DHT22' | 'DHT11' | 'PMS5003' | 'BME680' | 'BME688'

export type PitStatus = 'active' | 'inactive' | 'maintenance'

export interface Workshop {
  id: number
  name: string
  slug: string
  contact_email: string | null
  contact_phone: string | null
  created_at: string
}

// ─── API response wrappers ────────────────────────────────────────────────────

export interface ApiSuccessResponse<T> {
  success: true
  data: T
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

export interface ApiError {
  detail: string | { code: string; message: string }
}

// ─── Constants ────────────────────────────────────────────────────────────────

export const WORK_TYPE_OPTIONS: WorkType[] = [
  'Full PPF',
  'Partial PPF',
  'Ceramic Coating',
  'Custom',
]

export const WORK_TYPE_DURATION_MINUTES: Record<WorkType, number> = {
  'Full PPF': 360,
  'Partial PPF': 180,
  'Ceramic Coating': 240,
  'Custom': 0,
}

// Valid status transitions (mirrors backend JOB_STATUS_TRANSITIONS)
export const ALLOWED_TRANSITIONS: Record<JobStatus, JobStatus[]> = {
  waiting: ['in_progress', 'cancelled'],
  in_progress: ['quality_check', 'cancelled'],
  quality_check: ['completed', 'in_progress', 'cancelled'],
  completed: [],
  cancelled: [],
}

export const JOB_STATUS_LABELS: Record<JobStatus, string> = {
  waiting: 'Waiting',
  in_progress: 'In Progress',
  quality_check: 'Quality Check',
  completed: 'Completed',
  cancelled: 'Cancelled',
}
