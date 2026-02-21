import { clsx } from 'clsx'
import type { SensorStatus } from '@/types/common'
import { STATUS_COLORS } from '@/utils/sensorColors'
import { STATUS_LABELS } from '@/utils/constants'

interface SensorStatusBadgeProps {
  status: SensorStatus
  className?: string
  showDot?: boolean
}

export function SensorStatusBadge({ status, className, showDot = true }: SensorStatusBadgeProps) {
  const colors = STATUS_COLORS[status]
  return (
    <span
      className={clsx(
        'inline-flex items-center gap-1.5 px-2 py-0.5 rounded-full text-xs font-medium',
        colors.bg,
        colors.text,
        className,
      )}
    >
      {showDot && (
        <span className={clsx('w-1.5 h-1.5 rounded-full', colors.dot)} />
      )}
      {STATUS_LABELS[status]}
    </span>
  )
}
