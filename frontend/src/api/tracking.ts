// Public tracking API — no auth header attached
import axios from 'axios'
import type { JobTrackingResponse } from '@/types'

const trackingClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
  timeout: 10_000,
})

export const trackingApi = {
  /** Public endpoint — no Authorization header. GET /track/{view_token} */
  getJobByToken: async (viewToken: string): Promise<JobTrackingResponse> => {
    const resp = await trackingClient.get<JobTrackingResponse>(`/track/${viewToken}`)
    return resp.data
  },
}
