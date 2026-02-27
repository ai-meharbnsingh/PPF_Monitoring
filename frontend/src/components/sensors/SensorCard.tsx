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
        'card border transition-all duration-300 hover:scale-[1.01] overflow-hidden min-w-0',
        colors.border,
      )}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-white/[0.08]">
        <div>
          <h3 className="font-semibold text-white text-sm tracking-wide">{pit.name}</h3>
          <p className="text-xs text-gray-600 mt-0.5">Pit #{pit.pit_number}</p>
        </div>
        <div className="flex items-center gap-2">
          {isOnline ? (
            <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
              <Wifi className="h-3.5 w-3.5" />
              Live
            </span>
          ) : (
            <span className="flex items-center gap-1.5 text-xs text-gray-600">
              <WifiOff className="h-3.5 w-3.5" />
              Offline
            </span>
          )}
        </div>
      </div>

      {/* Sensor tiles grid */}
      <div className="grid grid-cols-2 gap-2 p-3 sm:p-4 min-w-0">
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
        {sensors?.pm1 != null && (
          <SensorTile
            metric="pm1"
            value={sensors.pm1}
            status={sensors?.pm25_status ?? 'unknown'}
          />
        )}
        {sensors?.pressure != null && (
          <SensorTile
            metric="pressure"
            value={sensors.pressure}
            status="good"
          />
        )}
        {sensors?.gas_resistance != null && (
          <SensorTile
            metric="gas_resistance"
            value={Math.round(sensors.gas_resistance / 1000)}
            status="good"
          />
        )}
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
      <div className="flex items-center justify-between px-4 py-2.5 border-t border-white/[0.08]">
        <span className="text-xs text-gray-600">
          {sensors?.last_reading_at
            ? `Updated ${formatRelative(sensors.last_reading_at)}`
            : 'No data'}
        </span>
        <Link
          to={`/admin/pits/${pit.id}`}
          className="flex items-center gap-1 text-xs text-electric-blue hover:text-white font-medium transition-colors"
        >
          Details
          <ChevronRight className="h-3 w-3" />
        </Link>
      </div>
    </div>
  )
}
