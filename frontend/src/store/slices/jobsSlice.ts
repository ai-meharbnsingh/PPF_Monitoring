import { createSlice, type PayloadAction } from '@reduxjs/toolkit'
import type { JobSummary, JobResponse } from '@/types/job'
import type { JobStatus } from '@/types/common'

interface Pagination {
  total: number
  page: number
  page_size: number
  total_pages: number
  has_next: boolean
  has_prev: boolean
}

interface JobFilters {
  status: JobStatus | null
  pit_id: number | null
}

interface JobsState {
  items: JobSummary[]
  currentJob: JobResponse | null
  pagination: Pagination
  filters: JobFilters
  isLoading: boolean
  error: string | null
}

const initialState: JobsState = {
  items: [],
  currentJob: null,
  pagination: {
    total: 0,
    page: 1,
    page_size: 20,
    total_pages: 0,
    has_next: false,
    has_prev: false,
  },
  filters: { status: null, pit_id: null },
  isLoading: false,
  error: null,
}

const jobsSlice = createSlice({
  name: 'jobs',
  initialState,
  reducers: {
    setJobs: (
      state,
      action: PayloadAction<{ items: JobSummary[]; pagination: Pagination }>,
    ) => {
      state.items = action.payload.items
      state.pagination = action.payload.pagination
      state.isLoading = false
      state.error = null
    },
    setCurrentJob: (state, action: PayloadAction<JobResponse | null>) => {
      state.currentJob = action.payload
    },
    addJob: (state, action: PayloadAction<JobSummary>) => {
      state.items.unshift(action.payload)
    },
    /** Called on WS job_status event — update status in the list */
    jobStatusUpdated: (
      state,
      action: PayloadAction<{
        job_id: number
        pit_id: number
        new_status: JobStatus
        previous_status: JobStatus | null
      }>,
    ) => {
      const { job_id, new_status } = action.payload
      const item = state.items.find((j) => j.id === job_id)
      if (item) {
        item.status = new_status
      }
      if (state.currentJob?.id === job_id) {
        state.currentJob.status = new_status
      }
    },
    setFilters: (state, action: PayloadAction<Partial<JobFilters>>) => {
      state.filters = { ...state.filters, ...action.payload }
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload
      state.isLoading = false
    },
  },
})

export const {
  setJobs,
  setCurrentJob,
  addJob,
  jobStatusUpdated,
  setFilters,
  setLoading: setJobsLoading,
  setError: setJobsError,
} = jobsSlice.actions
export default jobsSlice.reducer
