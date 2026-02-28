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
  const isOnline = sensors?.is_device_online ?? false
  // When offline, show gray/unknown status regardless of stored readings
  const worstStatus = isOnline ? (sensors ? getWorstStatus(sensors) : 'unknown') : 'unknown'
  const colors = STATUS_COLORS[worstStatus]

  return (
    <div
      className={clsx(
        'card border transition-all duration-300 hover:scale-[1.01] overflow-hidden min-w-0',
        colors.border,
        !isOnline && 'opacity-75',
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
            <span className="flex items-center gap-1.5 text-xs text-red-400 font-medium">
              <WifiOff className="h-3.5 w-3.5" />
              Device Offline
            </span>
          )}
        </div>
      </div>

      {/* Sensor tiles grid - show values only when online */}
      <div className="grid grid-cols-2 gap-2 p-3 sm:p-4 min-w-0 relative">
        {!isOnline && (
          <div className="absolute inset-0 bg-black/40 backdrop-blur-[1px] z-10 flex items-center justify-center">
            <div className="text-center">
              <WifiOff className="h-8 w-8 text-gray-500 mx-auto mb-2" />
              <p className="text-sm text-gray-400 font-medium">Device Offline</p>
              <p className="text-xs text-gray-600 mt-1">
                {sensors?.last_reading_at
                  ? `Last seen ${formatRelative(sensors.last_reading_at)}`
                  : 'No recent data'}
              </p>
            </div>
          </div>
        )}
        <SensorTile
          metric="temperature"
          value={sensors?.temperature ?? null}
          status={isOnline ? (sensors?.temp_status ?? 'unknown') : 'unknown'}
        />
        <SensorTile
          metric="humidity"
          value={sensors?.humidity ?? null}
          status={isOnline ? (sensors?.humidity_status ?? 'unknown') : 'unknown'}
        />
        <SensorTile
          metric="pm25"
          value={sensors?.pm25 ?? null}
          status={isOnline ? (sensors?.pm25_status ?? 'unknown') : 'unknown'}
        />
        <SensorTile
          metric="pm10"
          value={sensors?.pm10 ?? null}
          status={isOnline ? (sensors?.pm10_status ?? 'unknown') : 'unknown'}
        />
        {sensors?.pm1 != null && (
          <SensorTile
            metric="pm1"
            value={sensors.pm1}
            status={isOnline ? (sensors?.pm25_status ?? 'unknown') : 'unknown'}
          />
        )}
        {sensors?.pressure != null && (
          <SensorTile
            metric="pressure"
            value={sensors.pressure}
            status={isOnline ? 'good' : 'unknown'}
          />
        )}
        {sensors?.gas_resistance != null && (
          <SensorTile
            metric="gas_resistance"
            value={Math.round(sensors.gas_resistance / 1000)}
            status={isOnline ? 'good' : 'unknown'}
          />
        )}
        {sensors?.iaq != null && (
          <SensorTile
            metric="iaq"
            value={sensors.iaq}
            status={isOnline ? (sensors.iaq_status ?? 'unknown') : 'unknown'}
            className="col-span-2"
          />
        )}
      </div>

      {/* Footer */}
      <div className="flex items-center justify-between px-4 py-2.5 border-t border-white/[0.08]">
        <span className="text-xs text-gray-600">
          {isOnline
            ? (sensors?.last_reading_at
                ? `Updated ${formatRelative(sensors.last_reading_at)}`
                : 'No data')
            : (sensors?.last_reading_at
                ? `Offline since ${formatRelative(sensors.last_reading_at)}`
                : 'Device offline')}
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
