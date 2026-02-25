import { clsx } from 'clsx'
import type { SensorStatus } from '@/types/common'
import { STATUS_COLORS } from '@/utils/sensorColors'
import { SENSOR_UNITS, SENSOR_LABELS } from '@/utils/constants'
import { formatSensorValue } from '@/utils/formatters'

interface SensorTileProps {
  metric: string
  value: number | null
  status: SensorStatus
  className?: string
}

export function SensorTile({ metric, value, status, className }: SensorTileProps) {
  const colors = STATUS_COLORS[status]
  const unit = SENSOR_UNITS[metric] ?? ''
  const label = SENSOR_LABELS[metric] ?? metric

  return (
    <div
      className={clsx(
        'flex flex-col gap-1 p-3 rounded-xl border transition-colors duration-300 overflow-hidden min-w-0',
        colors.bg,
        colors.border,
        className,
      )}
    >
      <span className={clsx('text-[11px] font-medium tracking-wide', colors.text)}>{label}</span>
      <div className="flex items-baseline gap-1 flex-wrap">
        <span className={clsx('text-lg sm:text-2xl font-bold whitespace-nowrap', colors.text)}>
          {value != null ? formatSensorValue(value) : '—'}
        </span>
        {value != null && (
          <span className={clsx('text-[10px] sm:text-xs opacity-60', colors.text)}>{unit}</span>
        )}
      </div>
    </div>
  )
}
