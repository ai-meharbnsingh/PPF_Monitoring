import apiClient from './client'
import type {
  UserResponse,
  UserCreate,
  UserUpdate,
  AdminResetPassword,
  AdminResetPasswordResponse,
  PaginatedResponse,
} from '@/types'

export const usersApi = {
  // Users list uses query param, not path param
  list: async (workshopId: number): Promise<PaginatedResponse<UserResponse>> => {
    const resp = await apiClient.get<any>('/users', {
      params: { workshop_id: workshopId },
    })
    const payload = resp.data
    if (payload?.data?.items !== undefined) return payload.data
    if (payload?.items !== undefined) return payload
    return { items: [], total: 0, page: 1, page_size: 50, total_pages: 1, has_next: false, has_prev: false }
  },

  // List all users across all workshops (Super Admin only)
  listAll: async (): Promise<PaginatedResponse<UserResponse>> => {
    const resp = await apiClient.get<any>('/users', {
      params: { page_size: 100 },  // Max allowed by backend
    })
    const payload = resp.data
    if (payload?.data?.items !== undefined) return payload.data
    if (payload?.items !== undefined) return payload
    return { items: [], total: 0, page: 1, page_size: 50, total_pages: 1, has_next: false, has_prev: false }
  },

  create: async (data: UserCreate): Promise<UserResponse> => {
    const resp = await apiClient.post<UserResponse>('/users', data)
    return resp.data
  },

  getUser: async (userId: number): Promise<UserResponse> => {
    const resp = await apiClient.get<UserResponse>(`/users/${userId}`)
    return resp.data
  },

  update: async (userId: number, data: UserUpdate): Promise<UserResponse> => {
    const resp = await apiClient.patch<UserResponse>(`/users/${userId}`, data)
    return resp.data
  },

  resetPassword: async (
    userId: number,
    data: AdminResetPassword,
  ): Promise<AdminResetPasswordResponse> => {
    const resp = await apiClient.post<AdminResetPasswordResponse>(
      `/users/${userId}/reset-password`,
      data,
    )
    return resp.data
  },

  deactivate: async (userId: number): Promise<void> => {
    await apiClient.delete(`/users/${userId}`)
  },
}
