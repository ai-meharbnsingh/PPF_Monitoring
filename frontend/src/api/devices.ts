import apiClient from './client'
import type {
  DeviceResponse,
  DeviceRegisterRequest,
  DeviceRegisterResponse,
  DeviceCommandRequest,
  DeviceCommandResponse,
  PaginatedResponse,
} from '@/types'

export const devicesApi = {
  list: async (workshopId: number): Promise<PaginatedResponse<DeviceResponse>> => {
    const resp = await apiClient.get<any>(
      `/workshops/${workshopId}/devices`,
    )
    const payload = resp.data

    // Check if it's the wrapped structure { success: true, data: { items: [] } } or flat
    if (payload?.data?.items) return payload.data
    if (payload?.items) return payload
    return { items: [], total: 0, page: 1, page_size: 50, total_pages: 1, has_next: false, has_prev: false }
  },

  register: async (
    workshopId: number,
    data: DeviceRegisterRequest,
  ): Promise<DeviceRegisterResponse> => {
    const resp = await apiClient.post<{ success: true; data: DeviceRegisterResponse }>(
      `/workshops/${workshopId}/devices`,
      data,
    )
    return resp.data.data
  },

  getDevice: async (deviceId: string): Promise<DeviceResponse> => {
    const resp = await apiClient.get<DeviceResponse>(`/devices/${deviceId}`)
    return resp.data
  },

  sendCommand: async (
    deviceId: string,
    data: DeviceCommandRequest,
  ): Promise<DeviceCommandResponse> => {
    // Route: POST /devices/{device_id}/command (singular)
    const resp = await apiClient.post<DeviceCommandResponse>(
      `/devices/${deviceId}/command`,
      data,
    )
    return resp.data
  },
}
