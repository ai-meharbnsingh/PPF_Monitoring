import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppSelector } from '@/hooks/useAppDispatch'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { PageSpinner } from '@/components/ui/Spinner'
import { Modal } from '@/components/ui/Modal'
import { Select } from '@/components/ui/Select'
import { Check, X, RefreshCw, Cpu } from 'lucide-react'
import { client } from '@/api/client'
import toast from 'react-hot-toast'

interface PendingDevice {
  device_id: string
  mac_address: string | null
  firmware_version: string | null
  status: string
  primary_sensor_code: string | null
  air_quality_sensor_code: string | null
  is_online: boolean
  last_seen: string | null
  created_at: string
  ip_address: string | null
}

interface Workshop {
  id: number
  name: string
}

export default function AdminPendingDevicesPage() {
  const navigate = useNavigate()
  const userRole = useAppSelector((s) => s.auth.user?.role)
  const [devices, setDevices] = useState<PendingDevice[]>([])
  const [workshops, setWorkshops] = useState<Workshop[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedDevice, setSelectedDevice] = useState<PendingDevice | null>(null)
  const [selectedWorkshop, setSelectedWorkshop] = useState<string>('')
  const [isApproving, setIsApproving] = useState(false)
  const [isRejecting, setIsRejecting] = useState(false)

  // Check super admin access
  useEffect(() => {
    if (userRole !== 'super_admin') {
      navigate('/dashboard')
    }
  }, [userRole, navigate])

  // Fetch pending devices and workshops
  const fetchData = async () => {
    try {
      // Fetch pending devices
      const devicesRes = await client.get('/admin/devices/pending')
      const devicesData = devicesRes.data
      
      // Fetch workshops for assignment
      const workshopsRes = await client.get('/workshops')
      const workshopsData = workshopsRes.data
      
      setDevices(devicesData.data?.items || [])
      setWorkshops(workshopsData.data?.items || [])
    } catch (error) {
      toast.error('Failed to fetch pending devices')
      console.error('Fetch error:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    // Refresh every 10 seconds
    const interval = setInterval(fetchData, 10000)
    return () => clearInterval(interval)
  }, [])

  const handleApprove = async () => {
    if (!selectedDevice || !selectedWorkshop) {
      toast.error('Please select a workshop')
      return
    }

    setIsApproving(true)
    try {
      const res = await client.post(`/admin/devices/${selectedDevice.device_id}/approve`, {
        workshop_id: parseInt(selectedWorkshop),
      })

      const data = res.data
      toast.success(`Device approved! License: ${data.license_key}`)
      setSelectedDevice(null)
      setSelectedWorkshop('')
      fetchData()
    } catch (error: any) {
      toast.error(error?.response?.data?.detail || 'Error approving device')
    } finally {
      setIsApproving(false)
    }
  }

  const handleReject = async (deviceId: string) => {
    if (!confirm('Are you sure you want to reject this device?')) return

    setIsRejecting(true)
    try {
      await client.post(`/admin/devices/${deviceId}/reject`, {
        reason: 'Rejected by admin',
      })
      toast.success('Device rejected')
      fetchData()
    } catch (error) {
      toast.error('Failed to reject device')
    } finally {
      setIsRejecting(false)
    }
  }

  if (loading) return <PageSpinner />

  return (
    <div className="p-6 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Pending Devices</h1>
          <p className="text-sm text-gray-500 mt-1">
            ESP32 devices awaiting approval and workshop assignment
          </p>
        </div>
        <Button
          variant="secondary"
          leftIcon={<RefreshCw className="h-4 w-4" />}
          onClick={fetchData}
        >
          Refresh
        </Button>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="card p-4">
          <p className="text-sm text-gray-500">Pending Devices</p>
          <p className="text-3xl font-bold text-white">{devices.length}</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-500">Online Pending</p>
          <p className="text-3xl font-bold text-emerald-400">
            {devices.filter((d) => d.is_online).length}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-500">Workshops Available</p>
          <p className="text-3xl font-bold text-electric-blue">{workshops.length}</p>
        </div>
      </div>

      {/* Devices List */}
      {devices.length === 0 ? (
        <div className="card p-8 text-center">
          <Cpu className="h-12 w-12 text-gray-600 mx-auto mb-4" />
          <p className="text-white font-medium">No pending devices</p>
          <p className="text-sm text-gray-500 mt-2">
            New ESP32 devices will appear here when they connect and announce themselves.
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {devices.map((device) => (
            <div key={device.device_id} className="card p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  {/* Device ID and Status */}
                  <div className="flex items-center gap-3 mb-2">
                    <Cpu className="h-5 w-5 text-electric-blue" />
                    <span className="font-mono font-semibold text-white">
                      {device.device_id}
                    </span>
                    {device.is_online ? (
                      <Badge variant="success">Online</Badge>
                    ) : (
                      <Badge variant="default">Offline</Badge>
                    )}
                    <Badge variant="warning">Pending</Badge>
                  </div>

                  {/* Device Details */}
                  <div className="text-sm text-gray-500 space-y-1">
                    {device.mac_address && (
                      <p>MAC: {device.mac_address}</p>
                    )}
                    {device.ip_address && (
                      <p>IP: {device.ip_address}</p>
                    )}
                    {device.firmware_version && (
                      <p>Firmware: v{device.firmware_version}</p>
                    )}
                    <p>
                      Sensors: {device.primary_sensor_code || 'Unknown'}
                      {device.air_quality_sensor_code && ` + ${device.air_quality_sensor_code}`}
                    </p>
                    {device.last_seen && (
                      <p>Last seen: {new Date(device.last_seen).toLocaleString()}</p>
                    )}
                    <p>Announced: {new Date(device.created_at).toLocaleString()}</p>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-2">
                  <Button
                    size="sm"
                    leftIcon={<Check className="h-4 w-4" />}
                    onClick={() => setSelectedDevice(device)}
                  >
                    Approve
                  </Button>
                  <Button
                    size="sm"
                    variant="danger"
                    leftIcon={<X className="h-4 w-4" />}
                    onClick={() => handleReject(device.device_id)}
                    isLoading={isRejecting}
                  >
                    Reject
                  </Button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Approve Modal */}
      <Modal
        isOpen={!!selectedDevice}
        onClose={() => {
          setSelectedDevice(null)
          setSelectedWorkshop('')
        }}
        title={`Approve Device: ${selectedDevice?.device_id}`}
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-400">
            Select a workshop to assign this device to. A license key will be auto-generated.
          </p>

          <Select
            label="Workshop"
            value={selectedWorkshop}
            onChange={(e) => setSelectedWorkshop(e.target.value)}
            options={[
              { value: '', label: 'Select a workshop...' },
              ...workshops.map((w) => ({ value: String(w.id), label: w.name })),
            ]}
          />

          {selectedDevice && (
            <div className="bg-black/30 p-3 rounded-lg text-sm">
              <p className="text-gray-500">Device Details:</p>
              <p className="text-white font-mono">{selectedDevice.device_id}</p>
              <p className="text-gray-400">
                {selectedDevice.primary_sensor_code} 
                {selectedDevice.air_quality_sensor_code && ` + ${selectedDevice.air_quality_sensor_code}`}
              </p>
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <Button
              className="flex-1"
              onClick={handleApprove}
              isLoading={isApproving}
              disabled={!selectedWorkshop}
            >
              Approve & Assign
            </Button>
            <Button
              variant="secondary"
              onClick={() => {
                setSelectedDevice(null)
                setSelectedWorkshop('')
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
