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
}
