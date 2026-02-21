import apiClient from './client'
import type { LatestSensorSummary, PaginatedResponse, SensorReadingResponse, SensorStatsResponse } from '@/types'

export interface SensorHistoryParams {
  page?: number
  page_size?: number
  from_dt?: string
  to_dt?: string
}

export const sensorsApi = {
  /** Latest readings for all pits in a workshop (returns plain array) */
  latestForWorkshop: async (workshopId: number): Promise<LatestSensorSummary[]> => {
    const resp = await apiClient.get<LatestSensorSummary[]>(
      `/workshops/${workshopId}/sensors/latest`,
    )
    return resp.data
  },

  /** Latest reading for a single pit */
  latestForPit: async (pitId: number): Promise<LatestSensorSummary> => {
    const resp = await apiClient.get<LatestSensorSummary>(`/pits/${pitId}/sensors/latest`)
    return resp.data
  },

  /** Paginated sensor history for a pit */
  history: async (
    pitId: number,
    params?: SensorHistoryParams,
  ): Promise<PaginatedResponse<SensorReadingResponse>> => {
    const resp = await apiClient.get<PaginatedResponse<SensorReadingResponse>>(
      `/pits/${pitId}/sensors/history`,
      { params },
    )
    return resp.data
  },

  /** Aggregate stats for a pit over the last N hours */
  stats: async (pitId: number, hours = 24): Promise<SensorStatsResponse> => {
    const resp = await apiClient.get<SensorStatsResponse>(`/pits/${pitId}/sensors/stats`, {
      params: { hours },
    })
    return resp.data
  },
}
