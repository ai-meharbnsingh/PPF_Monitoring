import { Link } from 'react-router-dom'
import { Car, MapPin, Calendar } from 'lucide-react'
import type { JobSummary } from '@/types/job'
import { JobStatusBadge } from './JobStatusBadge'
import { formatDate, formatCurrency } from '@/utils/formatters'

interface JobCardProps {
  job: JobSummary
}

export function JobCard({ job }: JobCardProps) {
  return (
    <Link
      to={`/jobs/${job.id}`}
      className="block bg-white rounded-xl border border-gray-200 p-4 hover:border-blue-300 hover:shadow-sm transition-all"
    >
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Car info */}
          <div className="flex items-center gap-2 mb-2">
            <Car className="h-4 w-4 text-gray-400 shrink-0" />
            <span className="font-semibold text-gray-900 truncate">
              {job.car_model ?? 'Unknown vehicle'}
            </span>
            {job.car_plate && (
              <span className="text-xs text-gray-500 bg-gray-100 px-2 py-0.5 rounded font-mono">
                {job.car_plate}
              </span>
            )}
          </div>

          {/* Meta row */}
          <div className="flex flex-wrap items-center gap-3 text-xs text-gray-500">
            <span className="font-medium text-gray-700">{job.work_type}</span>
            {job.pit_name && (
              <span className="flex items-center gap-1">
                <MapPin className="h-3 w-3" />
                {job.pit_name}
              </span>
            )}
            {job.scheduled_start_time && (
              <span className="flex items-center gap-1">
                <Calendar className="h-3 w-3" />
                {formatDate(job.scheduled_start_time, 'dd MMM, HH:mm')}
              </span>
            )}
            {job.customer_name && (
              <span className="text-gray-600">Customer: {job.customer_name}</span>
            )}
          </div>
        </div>

        <div className="flex flex-col items-end gap-2 shrink-0">
          <JobStatusBadge status={job.status} />
          {job.quoted_price != null && (
            <span className="text-sm font-semibold text-gray-700">
              {formatCurrency(job.quoted_price, job.currency)}
            </span>
          )}
        </div>
      </div>
    </Link>
  )
}
