import { useEffect, useState, useCallback } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useAppDispatch'
import { setDevices, setDevicesLoading } from '@/store/slices/devicesSlice'
import { devicesApi } from '@/api/devices'
import { DeviceCard } from '@/components/devices/DeviceCard'
import { DeviceCommandModal } from '@/components/devices/DeviceCommandModal'
import { DeviceRegisterModal } from '@/components/devices/DeviceRegisterModal'
import { Skeleton } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { Cpu, Plus, RefreshCw } from 'lucide-react'
import type { DeviceResponse } from '@/types/device'

export default function DevicesPage() {
  const dispatch = useAppDispatch()
  const workshopId = useAppSelector((s) => s.auth.user?.workshop_id)
  const { items, isLoading } = useAppSelector((s) => s.devices)
  const [commandDevice, setCommandDevice] = useState<DeviceResponse | null>(null)
  const [registerOpen, setRegisterOpen] = useState(false)

  const loadDevices = useCallback(async () => {
    if (!workshopId) return
    dispatch(setDevicesLoading(true))
    try {
      const resp = await devicesApi.list(workshopId)
      dispatch(setDevices(resp.items))
    } catch {
      // silently handle — auth interceptor handles 401
    } finally {
      dispatch(setDevicesLoading(false))
    }
  }, [workshopId, dispatch])

  useEffect(() => {
    void loadDevices()
  }, [loadDevices])

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Devices</h1>
        <div className="flex gap-2">
          <Button
            size="sm"
            variant="secondary"
            isLoading={isLoading}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
            onClick={loadDevices}
          >
            Refresh
          </Button>
          <Button
            size="sm"
            leftIcon={<Plus className="h-4 w-4" />}
            onClick={() => setRegisterOpen(true)}
          >
            Register
          </Button>
        </div>
      </div>

      {isLoading && items.length === 0 ? (
        <div className="space-y-3">
          {[1, 2].map((i) => <Skeleton key={i} className="h-24" />)}
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={<Cpu className="h-12 w-12" />}
          title="No devices registered"
          description="Register your first ESP32 device to start collecting sensor data."
          action={
            <Button
              size="sm"
              leftIcon={<Plus className="h-4 w-4" />}
              onClick={() => setRegisterOpen(true)}
            >
              Register Device
            </Button>
          }
        />
      ) : (
        <div className="space-y-3">
          {items.map((device) => (
            <DeviceCard
              key={device.device_id}
              device={device}
              onSendCommand={setCommandDevice}
            />
          ))}
        </div>
      )}

      <DeviceCommandModal
        isOpen={!!commandDevice}
        onClose={() => setCommandDevice(null)}
        device={commandDevice}
      />
      <DeviceRegisterModal
        isOpen={registerOpen}
        onClose={() => setRegisterOpen(false)}
        onRegistered={loadDevices}
      />
    </div>
  )
}
