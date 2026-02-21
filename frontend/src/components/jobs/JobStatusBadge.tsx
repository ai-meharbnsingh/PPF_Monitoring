import { clsx } from 'clsx'
import type { JobStatus } from '@/types/common'
import { JOB_STATUS_COLORS } from '@/utils/sensorColors'
import { JOB_STATUS_LABELS } from '@/types/common'

interface JobStatusBadgeProps {
  status: JobStatus
  className?: string
}

export function JobStatusBadge({ status, className }: JobStatusBadgeProps) {
  const colors = JOB_STATUS_COLORS[status]
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-semibold',
        colors.bg,
        colors.text,
        className,
      )}
    >
      <span className={clsx('w-1.5 h-1.5 rounded-full', colors.dot)} />
      {JOB_STATUS_LABELS[status]}
    </span>
  )
}
