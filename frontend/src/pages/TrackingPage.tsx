import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { trackingApi } from '@/api/tracking'
import type { JobTrackingResponse } from '@/types/job'
import { JobStatusFlow } from '@/components/jobs/JobStatusFlow'
import { JobStatusBadge } from '@/components/jobs/JobStatusBadge'
import { Spinner } from '@/components/ui/Spinner'
import { Car, MapPin, Clock, CheckCircle } from 'lucide-react'
import { formatDate, getRemainingMinutes, formatDurationMinutes } from '@/utils/formatters'

export default function TrackingPage() {
  const { token } = useParams<{ token: string }>()
  const [job, setJob] = useState<JobTrackingResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [remaining, setRemaining] = useState<number | null>(null)

  const fetchJob = async () => {
    if (!token) return
    try {
      const data = await trackingApi.getJobByToken(token)
      setJob(data)
      setRemaining(getRemainingMinutes(data.estimated_end_time))
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 404) setNotFound(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void fetchJob()
    // Poll every 60 seconds
    const id = setInterval(() => void fetchJob(), 60_000)
    return () => clearInterval(id)
  }, [token])

  // Live countdown
  useEffect(() => {
    if (job?.status === 'completed' || job?.status === 'cancelled') return
    const id = setInterval(() => {
      setRemaining(getRemainingMinutes(job?.estimated_end_time ?? null))
    }, 60_000)
    return () => clearInterval(id)
  }, [job])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Spinner size="lg" label="Loading job status…" />
      </div>
    )
  }

  if (notFound || !job) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center p-8 text-center">
        <div className="text-6xl mb-4">🔍</div>
        <h1 className="text-2xl font-bold text-gray-800 mb-2">Job not found</h1>
        <p className="text-gray-500">
          This tracking link is invalid or has expired.
        </p>
      </div>
    )
  }

  const isComplete = job.status === 'completed'
  const isCancelled = job.status === 'cancelled'

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-slate-100">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4">
        <div className="max-w-lg mx-auto flex items-center justify-between">
          <div>
            <div className="flex items-center gap-2">
              <div className="h-7 w-7 rounded-lg bg-blue-600 flex items-center justify-center">
                <span className="text-white font-bold text-xs">PPF</span>
              </div>
              <span className="font-semibold text-gray-900">
                {job.workshop_name ?? 'PPF Workshop'}
              </span>
            </div>
          </div>
          <JobStatusBadge status={job.status} />
        </div>
      </div>

      <div className="max-w-lg mx-auto px-6 py-8 space-y-5">
        {/* Completed banner */}
        {isComplete && (
          <div className="flex items-center gap-3 p-4 bg-green-50 border border-green-200 rounded-xl">
            <CheckCircle className="h-6 w-6 text-green-600 shrink-0" />
            <div>
              <p className="font-semibold text-green-800">Your car is ready!</p>
              <p className="text-sm text-green-700">
                Work completed on {formatDate(job.actual_end_time)}
              </p>
            </div>
          </div>
        )}

        {/* Cancelled banner */}
        {isCancelled && (
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl">
            <p className="font-semibold text-red-800">Job Cancelled</p>
          </div>
        )}

        {/* Vehicle info */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <Car className="h-4 w-4 text-gray-400" />
            Your Vehicle
          </h2>
          <div className="space-y-2 text-sm">
            {job.car_model && (
              <div className="flex justify-between">
                <span className="text-gray-500">Model</span>
                <span className="font-medium">{job.car_model}</span>
              </div>
            )}
            {job.car_plate && (
              <div className="flex justify-between">
                <span className="text-gray-500">Plate</span>
                <span className="font-mono font-medium">{job.car_plate}</span>
              </div>
            )}
            <div className="flex justify-between">
              <span className="text-gray-500">Service</span>
              <span className="font-medium">{job.work_type}</span>
            </div>
          </div>
        </div>

        {/* Progress */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-800 mb-4">Progress</h2>
          <JobStatusFlow status={job.status} />
        </div>

        {/* Times */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
            <Clock className="h-4 w-4 text-gray-400" />
            Timing
          </h2>
          <div className="space-y-2 text-sm">
            {job.scheduled_start_time && (
              <div className="flex justify-between">
                <span className="text-gray-500">Scheduled</span>
                <span className="font-medium">{formatDate(job.scheduled_start_time)}</span>
              </div>
            )}
            {job.actual_start_time && (
              <div className="flex justify-between">
                <span className="text-gray-500">Started</span>
                <span className="font-medium">{formatDate(job.actual_start_time)}</span>
              </div>
            )}
            {job.estimated_end_time && !isComplete && !isCancelled && (
              <div className="flex justify-between">
                <span className="text-gray-500">Est. Completion</span>
                <span className="font-medium">{formatDate(job.estimated_end_time)}</span>
              </div>
            )}
            {remaining != null && !isComplete && !isCancelled && (
              <div className="flex justify-between bg-blue-50 -mx-3 px-3 py-2 rounded-lg mt-2">
                <span className="text-blue-700 font-medium">Time Remaining</span>
                <span className="text-blue-800 font-bold">
                  {remaining === 0 ? 'Almost done!' : formatDurationMinutes(remaining)}
                </span>
              </div>
            )}
          </div>
        </div>

        {/* Location */}
        {job.pit_display_name && (
          <div className="card p-5">
            <h2 className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
              <MapPin className="h-4 w-4 text-gray-400" />
              Location
            </h2>
            <p className="text-sm text-gray-700">{job.pit_display_name}</p>
          </div>
        )}

        <p className="text-center text-xs text-gray-400 pb-4">
          This page auto-refreshes every 60 seconds
        </p>
      </div>
    </div>
  )
}
