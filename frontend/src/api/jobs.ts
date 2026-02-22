import apiClient from './client'
import type {
  JobResponse,
  JobSummary,
  JobCreate,
  JobStatusUpdate,
  JobAssignStaff,
  PaginatedResponse,
} from '@/types'

export interface JobListParams {
  page?: number
  page_size?: number
  status?: string
  pit_id?: number
}

export const jobsApi = {
  list: async (
    workshopId: number,
    params?: JobListParams,
  ): Promise<PaginatedResponse<JobSummary>> => {
    const resp = await apiClient.get<any>(
      `/workshops/${workshopId}/jobs`,
      { params },
    )
    const payload = resp.data
    if (payload?.data?.items !== undefined) return payload.data
    if (payload?.items !== undefined) return payload
    return { items: [], total: 0, page: 1, page_size: 20, total_pages: 1, has_next: false, has_prev: false }
  },

  create: async (workshopId: number, data: JobCreate): Promise<JobResponse> => {
    const resp = await apiClient.post<any>(`/workshops/${workshopId}/jobs`, data)
    const payload = resp.data
    return payload?.data ?? payload
  },

  getJob: async (jobId: number): Promise<JobResponse> => {
    const resp = await apiClient.get<any>(`/jobs/${jobId}`)
    const payload = resp.data
    return payload?.data ?? payload
  },

  updateStatus: async (jobId: number, data: JobStatusUpdate): Promise<JobResponse> => {
    // Backend uses POST (not PATCH) for status transitions
    const resp = await apiClient.post<any>(`/jobs/${jobId}/status`, data)
    const payload = resp.data
    return payload?.data ?? payload
  },

  assignStaff: async (jobId: number, data: JobAssignStaff): Promise<JobResponse> => {
    const resp = await apiClient.patch<any>(`/jobs/${jobId}/assign-staff`, data)
    const payload = resp.data
    return payload?.data ?? payload
  },
}
