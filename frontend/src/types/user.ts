import type { UserRole } from './common'

// ─── User summary (list view) ─────────────────────────────────────────────────
export interface UserSummary {
  id: number
  username: string
  role: UserRole
  first_name: string | null
  last_name: string | null
  email: string | null
  phone: string | null
  workshop_id: number | null
  is_active: boolean
  is_temporary_password: boolean
  last_login: string | null
  created_at: string
}

// Full user (same as summary for now)
export type UserResponse = UserSummary

// ─── Create user request ──────────────────────────────────────────────────────
export interface UserCreate {
  username: string
  password: string
  role: Extract<UserRole, 'staff' | 'owner'>
  first_name?: string
  last_name?: string
  email?: string
  phone?: string
  workshop_id?: number
}

// ─── Update user ──────────────────────────────────────────────────────────────
export interface UserUpdate {
  first_name?: string
  last_name?: string
  email?: string
  phone?: string
}

// ─── Admin reset password ─────────────────────────────────────────────────────
export interface AdminResetPassword {
  new_password?: string  // if not provided, backend generates temp password
}

export interface AdminResetPasswordResponse {
  message: string
  temporary_password?: string
}
