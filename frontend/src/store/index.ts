import { configureStore } from '@reduxjs/toolkit'
import authReducer from './slices/authSlice'
import pitsReducer from './slices/pitsSlice'
import jobsReducer from './slices/jobsSlice'
import alertsReducer from './slices/alertsSlice'
import devicesReducer from './slices/devicesSlice'

export const store = configureStore({
  reducer: {
    auth: authReducer,
    pits: pitsReducer,
    jobs: jobsReducer,
    alerts: alertsReducer,
    devices: devicesReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
