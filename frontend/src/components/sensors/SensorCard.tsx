import { Link } from 'react-router-dom'
import { clsx } from 'clsx'
import { Wifi, WifiOff, ChevronRight } from 'lucide-react'
import type { PitSummary } from '@/types/pit'
import type { LatestSensorSummary } from '@/types/sensor'
import { SensorTile } from './SensorTile'
import { STATUS_COLORS, getWorstStatus } from '@/utils/sensorColors'
import { formatRelative } from '@/utils/formatters'

interface SensorCardProps {
  pit: PitSummary
  sensors: LatestSensorSummary | undefined
}

export function SensorCard({ pit, sensors }: SensorCardProps) {
  const worstStatus = sensors ? getWorstStatus(sensors) : 'unknown'
  const colors = STATUS_COLORS[worstStatus]
  const isOnline = sensors?.is_device_online ?? false

  return (
    <div
      className={clsx(
        'card border-2 transition-all duration-300',
        colors.border,
        'hover:shadow-md',
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-gray-100">
        <div>
          <h3 className="font-semibold text-gray-900 text-sm">{pit.name}</h3>
          <p className="text-xs text-gray-400">Pit #{pit.pit_number}</p>
        </div>
        <div className="flex items-center gap-2">
          {isOnline ? (
            <span className="flex items-center gap-1 text-xs text-emerald-600 font-medium">
              <Wifi className="h-3.5 w-3.5" />
              Live
            </span>
          ) : (
            <span className="flex items-center gap-1 text-xs text-gray-400">
              <WifiOff className="h-3.5 w-3.5" />
              Offline
            </span>
          )}
        </div>
      </div>

      {/* Sensor tiles grid */}
      <div className="grid grid-cols-2 gap-2 p-4">
        <SensorTile
          metric="temperature"
          value={sensors?.temperature ?? null}
          status={sensors?.temp_status ?? 'unknown'}
        />
        <SensorTile
          metric="humidity"
          value={sensors?.humidity ?? null}
          status={sensors?.humidity_status ?? 'unknown'}
        />
        <SensorTile
          metric="pm25"
          value={sensors?.pm25 ?? null}
          status={sensors?.pm25_status ?? 'unknown'}
        />
        <SensorTile
          metric="pm10"
          value={sensors?.pm10 ?? null}
          status={sensors?.pm10_status ?? 'unknown'}
        />
        {sensors?.iaq != null && (
          <SensorTile
            metric="iaq"
            value={sensors.iaq}
            status={sensors.iaq_status}
            className="col-span-2"
          />
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-4 py-2 border-t border-gray-100">
        <span className="text-xs text-gray-400">
          {sensors?.last_reading_at
            ? `Updated ${formatRelative(sensors.last_reading_at)}`
            : 'No data'}
        </span>
        <Link
          to={`/pits/${pit.id}`}
          className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800 font-medium"
        >
          Details
          <ChevronRight className="h-3 w-3" />
        </Link>
      </div>
    </div>
  )
}
