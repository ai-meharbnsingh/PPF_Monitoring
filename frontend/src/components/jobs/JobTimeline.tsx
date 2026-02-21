import type { JobStatusHistoryEntry } from '@/types/job'
import { JobStatusBadge } from './JobStatusBadge'
import { formatDate } from '@/utils/formatters'

interface JobTimelineProps {
  history: JobStatusHistoryEntry[]
}

export function JobTimeline({ history }: JobTimelineProps) {
  if (history.length === 0) return null
  return (
    <div className="relative">
      {/* Vertical line */}
      <div className="absolute left-3.5 top-4 bottom-4 w-px bg-gray-200" />
      <div className="space-y-4">
        {[...history].reverse().map((entry, idx) => (
          <div key={entry.id} className="flex items-start gap-4 relative">
            {/* Timeline dot */}
            <div
              className={`relative z-10 w-7 h-7 rounded-full flex items-center justify-center text-xs font-bold text-white shrink-0 ${
                idx === 0 ? 'bg-blue-600' : 'bg-gray-300'
              }`}
            >
              {history.length - idx}
            </div>
            <div className="flex-1 pb-1">
              <div className="flex items-center gap-2 mb-1">
                <JobStatusBadge status={entry.new_status} />
                <span className="text-xs text-gray-400">{formatDate(entry.created_at)}</span>
              </div>
              {entry.notes && (
                <p className="text-sm text-gray-600 bg-gray-50 rounded-lg px-3 py-2">
                  {entry.notes}
                </p>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  )
}
