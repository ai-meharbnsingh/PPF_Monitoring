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
    const resp = await apiClient.get<PaginatedResponse<DeviceResponse>>(
      `/workshops/${workshopId}/devices`,
    )
    return resp.data
  },

  register: async (
    workshopId: number,
    data: DeviceRegisterRequest,
  ): Promise<DeviceRegisterResponse> => {
    const resp = await apiClient.post<{ success: true; data: DeviceRegisterResponse }>(
      `/devices`,
      { ...data, workshop_id: workshopId },
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
