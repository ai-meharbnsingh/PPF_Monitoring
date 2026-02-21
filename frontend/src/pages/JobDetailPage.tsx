import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '@/hooks/useAppDispatch'
import { setCurrentJob } from '@/store/slices/jobsSlice'
import { jobsApi } from '@/api/jobs'
import { JobStatusBadge } from '@/components/jobs/JobStatusBadge'
import { JobStatusFlow } from '@/components/jobs/JobStatusFlow'
import { JobTimeline } from '@/components/jobs/JobTimeline'
import { PageSpinner } from '@/components/ui/Spinner'
import { Button } from '@/components/ui/Button'
import { RoleGuard } from '@/components/auth/ProtectedRoute'
import { ArrowLeft, Car, User, Copy, Check } from 'lucide-react'
import { formatDate, formatCurrency, formatDurationMinutes } from '@/utils/formatters'
import { ALLOWED_TRANSITIONS, JOB_STATUS_LABELS } from '@/types/common'
import type { JobStatus } from '@/types/common'
import toast from 'react-hot-toast'

export default function JobDetailPage() {
  const { jobId } = useParams<{ jobId: string }>()
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const job = useAppSelector((s) => s.jobs.currentJob)
  const [loading, setLoading] = useState(true)
  const [transitioning, setTransitioning] = useState(false)
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    if (!jobId) return
    setLoading(true)
    jobsApi
      .getJob(Number(jobId))
      .then((j) => dispatch(setCurrentJob(j)))
      .catch(() => toast.error('Job not found'))
      .finally(() => setLoading(false))
    return () => {
      dispatch(setCurrentJob(null))
    }
  }, [jobId, dispatch])

  const handleTransition = async (newStatus: JobStatus) => {
    if (!job) return
    setTransitioning(true)
    try {
      const updated = await jobsApi.updateStatus(job.id, { status: newStatus })
      dispatch(setCurrentJob(updated))
      toast.success(`Status updated to ${JOB_STATUS_LABELS[newStatus]}`)
    } catch {
      toast.error('Failed to update status')
    } finally {
      setTransitioning(false)
    }
  }

  const handleCopyTrackingLink = () => {
    if (!job?.customer_view_token) return
    const url = `${window.location.origin}/track/${job.customer_view_token}`
    void navigator.clipboard.writeText(url).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
      toast.success('Tracking link copied!')
    })
  }

  if (loading) return <PageSpinner />
  if (!job) return null

  const allowedTransitions = ALLOWED_TRANSITIONS[job.status]

  return (
    <div className="p-6 max-w-4xl mx-auto">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 mb-5"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Jobs
      </button>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main column */}
        <div className="lg:col-span-2 space-y-5">
          {/* Header card */}
          <div className="card p-5">
            <div className="flex items-start justify-between mb-4">
              <div>
                <h1 className="text-lg font-bold text-gray-900">
                  {job.car_model ?? 'Job #' + job.id}
                </h1>
                {job.car_plate && (
                  <span className="text-sm font-mono text-gray-500 bg-gray-100 px-2 py-0.5 rounded mt-1 inline-block">
                    {job.car_plate}
                  </span>
                )}
              </div>
              <JobStatusBadge status={job.status} />
            </div>

            {/* Status pipeline */}
            <div className="mb-5">
              <JobStatusFlow status={job.status} />
            </div>

            {/* Status transition buttons */}
            {allowedTransitions.length > 0 && (
              <RoleGuard roles={['owner', 'super_admin', 'staff']}>
                <div className="flex flex-wrap gap-2">
                  {allowedTransitions.map((nextStatus) => (
                    <Button
                      key={nextStatus}
                      size="sm"
                      variant={nextStatus === 'cancelled' ? 'danger' : 'primary'}
                      isLoading={transitioning}
                      onClick={() => void handleTransition(nextStatus)}
                    >
                      → {JOB_STATUS_LABELS[nextStatus]}
                    </Button>
                  ))}
                </div>
              </RoleGuard>
            )}
          </div>

          {/* Job details */}
          <div className="card p-5">
            <h2 className="font-semibold text-gray-800 mb-4">Job Details</h2>
            <dl className="grid grid-cols-2 gap-x-4 gap-y-3 text-sm">
              <div>
                <dt className="text-gray-500">Work Type</dt>
                <dd className="font-medium text-gray-900">{job.work_type}</dd>
              </div>
              {job.car_color && (
                <div>
                  <dt className="text-gray-500">Color</dt>
                  <dd className="font-medium text-gray-900">{job.car_color}</dd>
                </div>
              )}
              {job.quoted_price != null && (
                <div>
                  <dt className="text-gray-500">Price</dt>
                  <dd className="font-medium text-gray-900">
                    {formatCurrency(job.quoted_price, job.currency)}
                  </dd>
                </div>
              )}
              {job.estimated_duration_minutes && (
                <div>
                  <dt className="text-gray-500">Duration</dt>
                  <dd className="font-medium text-gray-900">
                    {formatDurationMinutes(job.estimated_duration_minutes)}
                  </dd>
                </div>
              )}
              {job.scheduled_start_time && (
                <div>
                  <dt className="text-gray-500">Scheduled</dt>
                  <dd className="font-medium text-gray-900">
                    {formatDate(job.scheduled_start_time)}
                  </dd>
                </div>
              )}
              {job.actual_start_time && (
                <div>
                  <dt className="text-gray-500">Started</dt>
                  <dd className="font-medium text-gray-900">
                    {formatDate(job.actual_start_time)}
                  </dd>
                </div>
              )}
              {job.estimated_end_time && (
                <div>
                  <dt className="text-gray-500">Est. End</dt>
                  <dd className="font-medium text-gray-900">
                    {formatDate(job.estimated_end_time)}
                  </dd>
                </div>
              )}
              {job.actual_end_time && (
                <div>
                  <dt className="text-gray-500">Completed</dt>
                  <dd className="font-medium text-green-700 font-semibold">
                    {formatDate(job.actual_end_time)}
                  </dd>
                </div>
              )}
            </dl>

            {job.work_description && (
              <div className="mt-4 pt-4 border-t border-gray-100">
                <p className="text-xs text-gray-500 mb-1">Description</p>
                <p className="text-sm text-gray-700">{job.work_description}</p>
              </div>
            )}

            {job.owner_notes && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <p className="text-xs text-gray-500 mb-1">Notes</p>
                <p className="text-sm text-gray-700">{job.owner_notes}</p>
              </div>
            )}
          </div>

          {/* Timeline */}
          {job.status_history.length > 0 && (
            <div className="card p-5">
              <h2 className="font-semibold text-gray-800 mb-4">Status History</h2>
              <JobTimeline history={job.status_history} />
            </div>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-5">
          {/* Customer */}
          {job.customer && (
            <div className="card p-4">
              <h2 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
                <User className="h-4 w-4 text-gray-400" />
                Customer
              </h2>
              <p className="text-sm font-medium text-gray-900">
                {job.customer.first_name
                  ? `${job.customer.first_name} ${job.customer.last_name ?? ''}`.trim()
                  : job.customer.username}
              </p>
              {job.customer.phone && (
                <p className="text-sm text-gray-500 mt-1">{job.customer.phone}</p>
              )}
              {job.customer.email && (
                <p className="text-sm text-gray-500">{job.customer.email}</p>
              )}
            </div>
          )}

          {/* Tracking link */}
          {job.customer_view_token && (
            <div className="card p-4">
              <h2 className="font-semibold text-gray-800 mb-3">Customer Tracking</h2>
              <p className="text-xs text-gray-500 mb-3">
                Share this link with the customer to let them track progress.
              </p>
              <Button
                variant="outline"
                size="sm"
                className="w-full"
                leftIcon={
                  copied ? (
                    <Check className="h-3.5 w-3.5 text-green-600" />
                  ) : (
                    <Copy className="h-3.5 w-3.5" />
                  )
                }
                onClick={handleCopyTrackingLink}
              >
                {copied ? 'Copied!' : 'Copy Tracking Link'}
              </Button>
            </div>
          )}

          {/* Car */}
          <div className="card p-4">
            <h2 className="font-semibold text-gray-800 mb-3 flex items-center gap-2">
              <Car className="h-4 w-4 text-gray-400" />
              Vehicle
            </h2>
            <dl className="space-y-1 text-sm">
              {job.car_model && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Model</dt>
                  <dd className="font-medium">{job.car_model}</dd>
                </div>
              )}
              {job.car_plate && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Plate</dt>
                  <dd className="font-mono font-medium">{job.car_plate}</dd>
                </div>
              )}
              {job.car_color && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Color</dt>
                  <dd className="font-medium">{job.car_color}</dd>
                </div>
              )}
              {job.car_year && (
                <div className="flex justify-between">
                  <dt className="text-gray-500">Year</dt>
                  <dd className="font-medium">{job.car_year}</dd>
                </div>
              )}
            </dl>
          </div>
        </div>
      </div>
    </div>
  )
}
