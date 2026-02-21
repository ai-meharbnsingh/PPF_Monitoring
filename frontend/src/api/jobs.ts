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
    const resp = await apiClient.get<PaginatedResponse<JobSummary>>(
      `/workshops/${workshopId}/jobs`,
      { params },
    )
    return resp.data
  },

  create: async (workshopId: number, data: JobCreate): Promise<JobResponse> => {
    const resp = await apiClient.post<JobResponse>(`/workshops/${workshopId}/jobs`, data)
    return resp.data
  },

  getJob: async (jobId: number): Promise<JobResponse> => {
    const resp = await apiClient.get<JobResponse>(`/jobs/${jobId}`)
    return resp.data
  },

  updateStatus: async (jobId: number, data: JobStatusUpdate): Promise<JobResponse> => {
    // Backend uses POST (not PATCH) for status transitions
    const resp = await apiClient.post<JobResponse>(`/jobs/${jobId}/status`, data)
    return resp.data
  },

  assignStaff: async (jobId: number, data: JobAssignStaff): Promise<JobResponse> => {
    const resp = await apiClient.patch<JobResponse>(`/jobs/${jobId}/assign-staff`, data)
    return resp.data
  },
}
