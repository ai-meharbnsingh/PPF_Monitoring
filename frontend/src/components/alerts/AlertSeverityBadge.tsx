import { clsx } from 'clsx'
import type { AlertSeverity } from '@/types/common'
import { SEVERITY_COLORS } from '@/utils/sensorColors'

interface AlertSeverityBadgeProps {
  severity: AlertSeverity
  className?: string
}

export function AlertSeverityBadge({ severity, className }: AlertSeverityBadgeProps) {
  const colors = SEVERITY_COLORS[severity]
  return (
    <span
      className={clsx(
        'inline-flex items-center px-2 py-0.5 rounded-full text-xs font-semibold capitalize',
        colors.bg,
        colors.text,
        className,
      )}
    >
      {severity}
    </span>
  )
}
