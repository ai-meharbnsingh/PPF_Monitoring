import apiClient from './client'
import type { PitSummary } from '@/types'

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
}
