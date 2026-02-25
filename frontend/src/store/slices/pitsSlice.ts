import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { PitSummary } from '@/types/pit'
import type { LatestSensorSummary } from '@/types/sensor'

interface PitsState {
  pits: PitSummary[]
  /** Key: pit_id → latest sensor summary (updated via REST poll or WS events) */
  sensorMap: Record<number, LatestSensorSummary>
  isLoading: boolean
  lastUpdated: string | null
  error: string | null
}

const initialState: PitsState = {
  pits: [],
  sensorMap: {},
  isLoading: false,
  lastUpdated: null,
  error: null,
}

const pitsSlice = createSlice({
  name: 'pits',
  initialState,
  reducers: {
    setPits: (state, action: PayloadAction<PitSummary[]>) => {
      state.pits = action.payload
      state.isLoading = false
      state.error = null
    },
    setSensorSummaries: (state, action: PayloadAction<LatestSensorSummary[]>) => {
      const map: Record<number, LatestSensorSummary> = {}
      action.payload.forEach((s) => {
        map[s.pit_id] = s
      })
      state.sensorMap = map
      state.lastUpdated = new Date().toISOString()
    },
    /** Called on WS sensor_update event */
    updateSensorData: (
      state,
      action: PayloadAction<{
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
      }>,
    ) => {
      const { pit_id, data } = action.payload
      const existing = state.sensorMap[pit_id]
      if (existing) {
        state.sensorMap[pit_id] = {
          ...existing,
          temperature: data.temperature,
          humidity: data.humidity,
          pm1: data.pm1,
          pm25: data.pm25,
          pm10: data.pm10,
          iaq: data.iaq,
          pressure: data.pressure,
          gas_resistance: data.gas_resistance,
          is_device_online: data.is_online,
          last_reading_at: data.recorded_at,
        }
      }
      state.lastUpdated = new Date().toISOString()
    },
    /** Called on WS device_offline event */
    deviceWentOffline: (
      state,
      action: PayloadAction<{ pit_id: number; device_id: string }>,
    ) => {
      const { pit_id } = action.payload
      if (state.sensorMap[pit_id]) {
        state.sensorMap[pit_id].is_device_online = false
      }
    },
    /** Called on WS device_online event */
    deviceCameOnline: (
      state,
      action: PayloadAction<{ pit_id: number; device_id: string }>,
    ) => {
      const { pit_id } = action.payload
      if (state.sensorMap[pit_id]) {
        state.sensorMap[pit_id].is_device_online = true
      }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    setError: (state, action: PayloadAction<string>) => {
      state.error = action.payload
      state.isLoading = false
    },
  },
})

export const {
  setPits,
  setSensorSummaries,
  updateSensorData,
  deviceWentOffline,
  deviceCameOnline,
  setLoading: setPitsLoading,
  setError: setPitsError,
} = pitsSlice.actions
export default pitsSlice.reducer
