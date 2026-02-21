import type { UserRole } from './common'

// ─── User Profile ─────────────────────────────────────────────────────────────

export interface UserProfile {
  id: number
  username: string
  role: UserRole
  workshop_id: number | null
  workshop_name: string | null
  first_name: string | null
  last_name: string | null
  email: string | null
  phone: string | null
  last_login: string | null
  is_temporary_password: boolean
  is_active: boolean
}

// ─── Auth API Request/Response shapes ─────────────────────────────────────────

export interface LoginRequest {
  username: string
  password: string
}

export interface LoginResponseData {
  access_token: string
  token_type: string
  user: Pick<
    UserProfile,
    | 'id'
    | 'username'
    | 'role'
    | 'workshop_id'
    | 'workshop_name'
    | 'first_name'
    | 'is_temporary_password'
  >
}

export interface TokenRefreshRequest {
  access_token: string
}

export interface TokenRefreshResponseData {
  access_token: string
  token_type: string
}

export interface ChangePasswordRequest {
  current_password: string
  new_password: string
}
