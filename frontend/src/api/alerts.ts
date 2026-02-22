import apiClient from './client'
import type {
  AlertResponse,
  AlertConfigResponse,
  AlertConfigUpdate,
  AlertAcknowledgeRequest,
  PaginatedResponse,
} from '@/types'

export interface AlertListParams {
  page?: number
  page_size?: number
  pit_id?: number
  unacknowledged_only?: boolean
}

export const alertsApi = {
  list: async (
    workshopId: number,
    params?: AlertListParams,
  ): Promise<PaginatedResponse<AlertResponse>> => {
    const resp = await apiClient.get<any>(
      `/workshops/${workshopId}/alerts`,
      { params },
    )
    const payload = resp.data
    if (payload?.data?.items !== undefined) return payload.data
    if (payload?.items !== undefined) return payload
    return { items: [], total: 0, page: 1, page_size: 20, total_pages: 1, has_next: false, has_prev: false }
  },

  acknowledge: async (
    alertId: number,
    data?: AlertAcknowledgeRequest,
  ): Promise<AlertResponse> => {
    const resp = await apiClient.post<AlertResponse>(`/alerts/${alertId}/acknowledge`, data ?? {})
    return resp.data
  },

  acknowledgeAll: async (workshopId: number, pitId?: number): Promise<void> => {
    await apiClient.post(
      `/workshops/${workshopId}/alerts/acknowledge-all`,
      {},
      { params: pitId ? { pit_id: pitId } : {} },
    )
  },

  getConfig: async (workshopId: number): Promise<AlertConfigResponse> => {
    const resp = await apiClient.get<AlertConfigResponse>(
      `/workshops/${workshopId}/alert-config`,
    )
    return resp.data
  },

  updateConfig: async (
    workshopId: number,
    data: AlertConfigUpdate,
  ): Promise<AlertConfigResponse> => {
    const resp = await apiClient.patch<AlertConfigResponse>(
      `/workshops/${workshopId}/alert-config`,
      data,
    )
    return resp.data
  },
}
