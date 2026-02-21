import { useState } from 'react'
import { Wifi, WifiOff, Terminal, Power, RotateCcw } from 'lucide-react'
import type { DeviceResponse } from '@/types/device'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { formatRelative } from '@/utils/formatters'
import { clsx } from 'clsx'

interface DeviceCardProps {
  device: DeviceResponse
  onSendCommand: (device: DeviceResponse) => void
}

export function DeviceCard({ device, onSendCommand }: DeviceCardProps) {
  const isOnline = device.is_online

  return (
    <div className={clsx('card p-4 transition-all', !isOnline && 'opacity-75')}>
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1 min-w-0">
          {/* Device ID + online status */}
          <div className="flex items-center gap-2 mb-1">
            {isOnline ? (
              <Wifi className="h-4 w-4 text-emerald-500 shrink-0" />
            ) : (
              <WifiOff className="h-4 w-4 text-gray-400 shrink-0" />
            )}
            <span className="font-mono font-semibold text-sm text-gray-900 truncate">
              {device.device_id}
            </span>
            <Badge
              variant={
                device.status === 'active'
                  ? 'success'
                  : device.status === 'disabled'
                  ? 'warning'
                  : device.status === 'suspended'
                  ? 'danger'
                  : 'default'
              }
            >
              {device.status}
            </Badge>
          </div>

          {/* Meta info */}
          <div className="text-xs text-gray-500 space-y-0.5">
            {device.pit_name && (
              <p>📍 {device.pit_name}</p>
            )}
            {device.primary_sensor_type_code && (
              <p>
                Sensors: {device.primary_sensor_type_code}
                {device.air_quality_sensor_type_code &&
                  ` + ${device.air_quality_sensor_type_code}`}
              </p>
            )}
            <p>
              {isOnline
                ? `Online · Last seen ${formatRelative(device.last_seen)}`
                : `Offline since ${formatRelative(device.last_seen)}`}
            </p>
            {device.firmware_version && (
              <p>Firmware: v{device.firmware_version}</p>
            )}
          </div>
        </div>

        {/* Commands */}
        <div className="flex flex-col gap-1 shrink-0">
          <Button
            size="sm"
            variant="secondary"
            leftIcon={<Terminal className="h-3.5 w-3.5" />}
            onClick={() => onSendCommand(device)}
          >
            Command
          </Button>
        </div>
      </div>
    </div>
  )
}
