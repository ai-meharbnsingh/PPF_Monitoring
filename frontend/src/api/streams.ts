import apiClient from './client'
import type { StreamTokenResponse, PitStreamStatus } from '@/types'

export const streamsApi = {
  getStreamToken: async (pitId: number): Promise<StreamTokenResponse> => {
    const resp = await apiClient.post<StreamTokenResponse>(`/pits/${pitId}/stream-token`)
    return resp.data
  },

  getStreamStatus: async (pitId: number): Promise<PitStreamStatus> => {
    const resp = await apiClient.get<PitStreamStatus>(`/pits/${pitId}/stream-status`)
    return resp.data
  },
}
