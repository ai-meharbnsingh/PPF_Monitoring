import { clsx } from 'clsx'
import type { SensorStatus } from '@/types/common'
import { STATUS_COLORS } from '@/utils/sensorColors'
import { SENSOR_UNITS, SENSOR_LABELS } from '@/utils/constants'
import { formatSensorValue } from '@/utils/formatters'

interface SensorTileProps {
  metric: string           // e.g. 'temperature', 'humidity', 'pm25'
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
        'flex flex-col gap-1 p-3 rounded-xl border-2 transition-colors duration-300',
        colors.bg,
        colors.border,
        className,
      )}
    >
      <span className={clsx('text-xs font-medium', colors.text)}>{label}</span>
      <div className="flex items-baseline gap-1">
        <span className={clsx('text-xl font-bold', colors.text)}>
          {value != null ? formatSensorValue(value) : '—'}
        </span>
        {value != null && (
          <span className={clsx('text-xs', colors.text, 'opacity-70')}>{unit}</span>
        )}
      </div>
    </div>
  )
}
