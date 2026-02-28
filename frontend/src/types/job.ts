import type { JobStatus, WorkType } from './common'

// ─── Customer embedded in job ─────────────────────────────────────────────────
export interface CustomerInJob {
  id: number
  username: string
  first_name: string | null
  last_name: string | null
  phone: string | null
  email: string | null
}

// ─── Status history entry ─────────────────────────────────────────────────────
export interface JobStatusHistoryEntry {
  id: number
  previous_status: JobStatus | null
  new_status: JobStatus
  changed_by_user_id: number | null
  notes: string | null
  created_at: string
}

// ─── Job summary (list view) ──────────────────────────────────────────────────
export interface JobSummary {
  id: number
  workshop_id: number
  pit_id: number
  pit_name: string | null
  car_model: string | null
  car_plate: string | null
  work_type: WorkType
  status: JobStatus
  quoted_price: number | null
  currency: string
  scheduled_start_time: string | null
  actual_start_time: string | null
  estimated_end_time: string | null
  actual_end_time: string | null
  created_at: string
  customer_name: string | null
  tracking_code: string | null
}

// ─── Full job response (detail view) ─────────────────────────────────────────
export interface JobResponse {
  id: number
  workshop_id: number
  pit_id: number
  customer_user_id: number | null
  car_model: string | null
  car_plate: string | null
  car_color: string | null
  car_year: number | null
  work_type: WorkType
  work_description: string | null
  estimated_duration_minutes: number | null
  status: JobStatus
  scheduled_start_time: string | null
  actual_start_time: string | null
  estimated_end_time: string | null
  actual_end_time: string | null
  quoted_price: number | null
  currency: string
  owner_notes: string | null
  staff_notes: string | null
  assigned_staff_ids: number[]
  customer_view_token: string | null
  customer_view_expires_at: string | null
  created_by_user_id: number | null
  created_at: string
  updated_at: string | null
  customer: CustomerInJob | null
  status_history: JobStatusHistoryEntry[]
}

// ─── Public tracking response (no auth) ──────────────────────────────────────
export interface JobTrackingResponse {
  job_id: number
  work_type: WorkType
  status: JobStatus
  car_model: string | null
  car_plate: string | null
  scheduled_start_time: string | null
  actual_start_time: string | null
  estimated_end_time: string | null
  actual_end_time: string | null
  pit_display_name: string | null
  workshop_name: string | null
}

// ─── Create job request ────────────────────────────────────────────────────────
export interface JobCreate {
  pit_id: number
  work_type: WorkType
  car_model?: string
  car_plate?: string
  car_color?: string
  car_year?: number
  work_description?: string
  estimated_duration_minutes?: number
  scheduled_start_time?: string
  customer_name?: string
  customer_phone?: string
  customer_email?: string
  quoted_price?: number
  currency?: string
  owner_notes?: string
}

// ─── Status update request ────────────────────────────────────────────────────
export interface JobStatusUpdate {
  status: JobStatus
  notes?: string
  staff_notes?: string
}

// ─── Assign staff request ─────────────────────────────────────────────────────
export interface JobAssignStaff {
  staff_user_ids: number[]
}
