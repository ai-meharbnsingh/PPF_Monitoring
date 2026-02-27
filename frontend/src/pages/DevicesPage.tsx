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
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import { Cpu, Plus, RefreshCw, ShieldCheck, MapPin } from 'lucide-react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { toast } from 'react-hot-toast'
import type { DeviceResponse } from '@/types/device'

export default function DevicesPage() {
  const dispatch = useAppDispatch()
  const queryClient = useQueryClient()
  const workshopId = useAppSelector((s) => s.auth.user?.workshop_id)
  const { items, isLoading } = useAppSelector((s) => s.devices)
  const [commandDevice, setCommandDevice] = useState<DeviceResponse | null>(null)
  const [registerOpen, setRegisterOpen] = useState(false)
  const [assigningDeviceId, setAssigningDeviceId] = useState<string | null>(null)
  const [assignPitId, setAssignPitId] = useState('')

  const loadDevices = useCallback(async () => {
    if (!workshopId) return
    dispatch(setDevicesLoading(true))
    try {
      const resp = await devicesApi.list(workshopId)
      dispatch(setDevices(resp.items))
    } catch {
      dispatch(setDevicesLoading(false))
    }
  }, [workshopId, dispatch])

  useEffect(() => {
    void loadDevices()
  }, [loadDevices])

  // Fetch pending devices
  const { data: pendingDevices, isLoading: pendingLoading } = useQuery({
    queryKey: ['pending_devices'],
    queryFn: devicesApi.listPending,
  })

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: ({ deviceId, wsId }: { deviceId: string; wsId: number }) =>
      devicesApi.approve(deviceId, wsId),
    onSuccess: (data) => {
      const licenseKey = data?.data?.license_key || data?.license_key || 'See device details'
      toast.success(`Device approved! License key: ${licenseKey}`, { duration: 8000 })
      queryClient.invalidateQueries({ queryKey: ['pending_devices'] })
      void loadDevices()
    },
    onError: (error: any) => {
      toast.error(
        error?.response?.data?.detail?.[0]?.msg ||
        error?.response?.data?.detail ||
        'Failed to approve device'
      )
    },
  })

  // Assign mutation
  const assignMutation = useMutation({
    mutationFn: ({ deviceId, wsId, pitId }: { deviceId: string; wsId: number; pitId: number }) =>
      devicesApi.assign(deviceId, wsId, pitId),
    onSuccess: () => {
      toast.success('Device assigned to pit successfully!')
      setAssigningDeviceId(null)
      setAssignPitId('')
      queryClient.invalidateQueries({ queryKey: ['pending_devices'] })
      void loadDevices()
    },
    onError: (error: any) => {
      toast.error(
        error?.response?.data?.detail?.[0]?.msg ||
        error?.response?.data?.detail ||
        'Failed to assign device'
      )
    },
  })

  const handleApprove = (deviceId: string) => {
    if (!workshopId) {
      toast.error('No workshop assigned to your account')
      return
    }
    approveMutation.mutate({ deviceId, wsId: workshopId })
  }

  const handleAssign = (deviceId: string) => {
    const pitId = parseInt(assignPitId)
    if (!workshopId || !pitId) {
      toast.error('Please enter a valid Pit ID')
      return
    }
    assignMutation.mutate({ deviceId, wsId: workshopId, pitId })
  }

  const pendingCount = pendingDevices?.length ?? 0

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

      {/* ── Pending Devices Section ── */}
      {pendingCount > 0 && (
        <Card className="bg-matte-black border-amber-500/30 mb-6">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg text-amber-400 flex items-center gap-2">
                <ShieldCheck className="h-5 w-5" />
                Pending Devices
              </CardTitle>
              <span className="inline-flex items-center justify-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-amber-500/20 text-amber-400 border border-amber-500/30">
                {pendingCount}
              </span>
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {pendingLoading ? (
              <p className="text-gray-400">Loading pending devices...</p>
            ) : (
              pendingDevices?.map((device) => (
                <div
                  key={device.device_id}
                  className="p-4 bg-white/[0.02] border border-white/[0.05] rounded-xl"
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0 flex-1">
                      <p className="font-semibold text-white truncate">{device.device_id}</p>
                      <div className="mt-1 space-y-0.5 text-sm text-gray-400">
                        {device.mac_address && (
                          <p>MAC: <span className="text-electric-blue">{device.mac_address}</span></p>
                        )}
                        {device.firmware_version && (
                          <p>Firmware: <span className="text-gray-300">{device.firmware_version}</span></p>
                        )}
                        {device.ip_address && (
                          <p>IP: <span className="text-gray-300">{device.ip_address}</span></p>
                        )}
                        {device.last_seen && (
                          <p>Last seen: <span className="text-gray-300">{new Date(device.last_seen).toLocaleString()}</span></p>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={() => handleApprove(device.device_id)}
                      disabled={approveMutation.isPending}
                      className="shrink-0 bg-electric-blue text-black font-semibold px-4 py-2 rounded-lg hover:bg-electric-blue/90 disabled:opacity-50 transition-colors text-sm"
                    >
                      {approveMutation.isPending ? 'Approving...' : 'Approve'}
                    </button>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      )}

      {/* ── Active Devices ── */}
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
            <div key={device.device_id}>
              <DeviceCard
                device={device}
                onSendCommand={setCommandDevice}
              />
              {/* Assign to Pit button for devices without a pit */}
              {!device.pit_id && (
                <div className="mt-1 ml-2 mb-3">
                  {assigningDeviceId === device.device_id ? (
                    <div className="flex items-center gap-2">
                      <input
                        type="number"
                        min={1}
                        value={assignPitId}
                        onChange={(e) => setAssignPitId(e.target.value)}
                        placeholder="Pit ID"
                        className="w-24 bg-black/40 border border-white/10 rounded-lg px-3 py-1.5 text-white text-sm focus:border-electric-blue focus:ring-1 focus:ring-electric-blue outline-none transition-all"
                      />
                      <button
                        onClick={() => handleAssign(device.device_id)}
                        disabled={assignMutation.isPending}
                        className="bg-electric-blue text-black font-semibold px-3 py-1.5 rounded-lg hover:bg-electric-blue/90 disabled:opacity-50 transition-colors text-sm"
                      >
                        {assignMutation.isPending ? 'Assigning...' : 'Confirm'}
                      </button>
                      <button
                        onClick={() => { setAssigningDeviceId(null); setAssignPitId('') }}
                        className="text-gray-400 hover:text-white text-sm px-2 py-1.5 transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => setAssigningDeviceId(device.device_id)}
                      className="flex items-center gap-1.5 text-sm text-amber-400 hover:text-amber-300 transition-colors"
                    >
                      <MapPin className="h-3.5 w-3.5" />
                      Assign to Pit
                    </button>
                  )}
                </div>
              )}
            </div>
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
