import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { DeviceResponse } from '@/types/device'

interface DevicesState {
  items: DeviceResponse[]
  isLoading: boolean
  error: string | null
}

const initialState: DevicesState = {
  items: [],
  isLoading: false,
  error: null,
}

const devicesSlice = createSlice({
  name: 'devices',
  initialState,
  reducers: {
    setDevices: (state, action: PayloadAction<DeviceResponse[]>) => {
      state.items = action.payload
      state.isLoading = false
      state.error = null
    },
    /** Update single device online status from WS event */
    updateDeviceOnlineStatus: (
      state,
      action: PayloadAction<{ device_id: string; is_online: boolean }>,
    ) => {
      const device = state.items.find((d) => d.device_id === action.payload.device_id)
      if (device) {
        device.is_online = action.payload.is_online
        if (!action.payload.is_online) {
          device.last_seen = new Date().toISOString()
        }
      }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
      state.isLoading = false
    },
  },
})

export const { setDevices, updateDeviceOnlineStatus, setLoading: setDevicesLoading } =
  devicesSlice.actions
export default devicesSlice.reducer
