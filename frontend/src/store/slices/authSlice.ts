import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { UserProfile } from '@/types/auth'
import { LS_TOKEN_KEY, LS_USER_KEY } from '@/utils/constants'

interface AuthState {
  user: UserProfile | null
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

// Rehydrate from localStorage on app init
function loadFromStorage(): Pick<AuthState, 'user' | 'token' | 'isAuthenticated'> {
  try {
    const token = localStorage.getItem(LS_TOKEN_KEY)
    const userRaw = localStorage.getItem(LS_USER_KEY)
    const user: UserProfile | null = userRaw ? (JSON.parse(userRaw) as UserProfile) : null
    return {
      token,
      user,
      isAuthenticated: !!token && !!user,
    }
  } catch {
    return { token: null, user: null, isAuthenticated: false }
  }
}

const initialState: AuthState = {
  ...loadFromStorage(),
  isLoading: false,
  error: null,
}

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    setCredentials: (
      state,
      action: PayloadAction<{ token: string; user: UserProfile }>,
    ) => {
      state.token = action.payload.token
      state.user = action.payload.user
      state.isAuthenticated = true
      state.isLoading = false
      state.error = null
      localStorage.setItem(LS_TOKEN_KEY, action.payload.token)
      localStorage.setItem(LS_USER_KEY, JSON.stringify(action.payload.user))
    },
    clearAuth: (state) => {
      state.token = null
      state.user = null
      state.isAuthenticated = false
      state.error = null
      localStorage.removeItem(LS_TOKEN_KEY)
      localStorage.removeItem(LS_USER_KEY)
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
      state.isLoading = false
    },
    /** Called after successful password change */
    clearTemporaryFlag: (state) => {
      if (state.user) {
        state.user.is_temporary_password = false
        localStorage.setItem(LS_USER_KEY, JSON.stringify(state.user))
      }
    },
  },
})

export const { setCredentials, clearAuth, setLoading, setError, clearTemporaryFlag } =
  authSlice.actions
export default authSlice.reducer
