import apiClient from './client'
import type { PitSummary } from '@/types'

export interface CreatePitPayload {
  pit_number: number
  name?: string
  description?: string
  camera_ip?: string
  camera_rtsp_url?: string
  camera_model?: string
  camera_username?: string
}

export const pitsApi = {
  listPits: async (workshopId: number): Promise<PitSummary[]> => {
    // Returns plain array (not paginated)
    const resp = await apiClient.get<PitSummary[]>(`/workshops/${workshopId}/pits`)
    return resp.data
  },

  getPit: async (pitId: number): Promise<PitSummary> => {
    const resp = await apiClient.get<PitSummary>(`/pits/${pitId}`)
    return resp.data
  },

  createPit: async (workshopId: number, payload: CreatePitPayload): Promise<PitSummary> => {
    const resp = await apiClient.post<PitSummary>(`/workshops/${workshopId}/pits`, payload)
    return resp.data
  },

  getAlertConfig: async (pitId: number): Promise<PitAlertConfigResponse> => {
    const resp = await apiClient.get<PitAlertConfigResponse>(`/pits/${pitId}/alert-config`)
    return resp.data
  },

  updateAlertConfig: async (pitId: number, data: PitAlertConfigUpdate): Promise<void> => {
    await apiClient.put(`/pits/${pitId}/alert-config`, data)
  },
}

export interface PitAlertConfigUpdate {
  temp_min?: number | null
  temp_max?: number | null
  humidity_max?: number | null
  pm25_warning?: number | null
  pm25_critical?: number | null
  pm10_warning?: number | null
  pm10_critical?: number | null
  iaq_warning?: number | null
  iaq_critical?: number | null
  device_offline_threshold_seconds?: number | null
}

export interface PitAlertConfigResponse {
  pit_id: number
  temp_min: number
  temp_min_source: string
  temp_max: number
  temp_max_source: string
  humidity_max: number
  humidity_max_source: string
  pm25_warning: number
  pm25_warning_source: string
  pm25_critical: number
  pm25_critical_source: string
  pm10_warning: number
  pm10_warning_source: string
  pm10_critical: number
  pm10_critical_source: string
  iaq_warning: number
  iaq_warning_source: string
  iaq_critical: number
  iaq_critical_source: string
  device_offline_threshold_seconds: number
  device_offline_threshold_seconds_source: string
}
