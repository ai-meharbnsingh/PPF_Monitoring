import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { AlertResponse, AlertConfigResponse } from '@/types/alert'
import type { WsAlertData } from '@/types/alert'

interface Pagination {
  total: number
  page: number
  total_pages: number
  has_next: boolean
}

interface AlertsState {
  items: AlertResponse[]
  unreadCount: number
  alertConfig: AlertConfigResponse | null
  pagination: Pagination
  isPanelOpen: boolean
  isLoading: boolean
}

const initialState: AlertsState = {
  items: [],
  unreadCount: 0,
  alertConfig: null,
  pagination: { total: 0, page: 1, total_pages: 0, has_next: false },
  isPanelOpen: false,
  isLoading: false,
}

const alertsSlice = createSlice({
  name: 'alerts',
  initialState,
  reducers: {
    setAlerts: (
      state,
      action: PayloadAction<{ items: AlertResponse[]; pagination: Pagination }>,
    ) => {
      state.items = action.payload.items
      state.pagination = action.payload.pagination
      state.unreadCount = action.payload.items.filter((a) => !a.is_acknowledged).length
      state.isLoading = false
    },
    /** Called on WS alert event — prepend to list and increment badge */
    newAlertReceived: (state, action: PayloadAction<WsAlertData & { pit_id: number | null }>) => {
      const data = action.payload
      // Create a minimal AlertResponse entry for the panel
      const alertItem: AlertResponse = {
        id: data.alert_id,
        workshop_id: 0, // filled by next REST fetch
        pit_id: data.pit_id,
        device_id: null,
        alert_type: data.alert_type,
        severity: data.severity,
        message: data.message,
        trigger_value: data.trigger_value,
        threshold_value: data.threshold_value,
        is_acknowledged: false,
        acknowledged_by_user_id: null,
        acknowledged_at: null,
        resolved_at: null,
        sms_sent: false,
        email_sent: false,
        created_at: new Date().toISOString(),
      }
      state.items.unshift(alertItem)
      state.unreadCount += 1
    },
    acknowledgeAlert: (state, action: PayloadAction<number>) => {
      const alert = state.items.find((a) => a.id === action.payload)
      if (alert && !alert.is_acknowledged) {
        alert.is_acknowledged = true
        alert.acknowledged_at = new Date().toISOString()
        state.unreadCount = Math.max(0, state.unreadCount - 1)
      }
    },
    acknowledgeAll: (state) => {
      state.items.forEach((a) => {
        a.is_acknowledged = true
      })
      state.unreadCount = 0
    },
    setAlertConfig: (state, action: PayloadAction<AlertConfigResponse>) => {
      state.alertConfig = action.payload
    },
    setPanelOpen: (state, action: PayloadAction<boolean>) => {
      state.isPanelOpen = action.payload
      // Clear badge when user opens panel
      if (action.payload) {
        state.unreadCount = state.items.filter((a) => !a.is_acknowledged).length
      }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
  },
})

export const {
  setAlerts,
  newAlertReceived,
  acknowledgeAlert,
  acknowledgeAll,
  setAlertConfig,
  setPanelOpen,
  setLoading: setAlertsLoading,
} = alertsSlice.actions
export default alertsSlice.reducer
