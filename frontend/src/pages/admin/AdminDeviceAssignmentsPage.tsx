import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAppSelector } from '@/hooks/useAppDispatch'
import { devicesApi } from '@/api/devices'
import { pitsApi } from '@/api/pits'
import type { PitSummary } from '@/types'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { PageSpinner } from '@/components/ui/Spinner'
import { Modal } from '@/components/ui/Modal'
import { Select } from '@/components/ui/Select'
import { RefreshCw, Cpu, Building2, User, MapPin, Unlink } from 'lucide-react'
import toast from 'react-hot-toast'

interface DeviceAssignment {
  device_id: string
  device_status: string
  is_online: boolean
  last_seen: string | null
  workshop_id: number | null
  workshop_name: string | null
  owner_username: string | null
  pit_id: number | null
  pit_name: string | null
  license_key: string | null
  primary_sensor_code: string | null
  air_quality_sensor_code: string | null
}

interface Workshop {
  id: number
  name: string
}

export default function AdminDeviceAssignmentsPage() {
  const navigate = useNavigate()
  const userRole = useAppSelector((s) => s.auth.user?.role)
  const [assignments, setAssignments] = useState<DeviceAssignment[]>([])
  const [workshops, setWorkshops] = useState<Workshop[]>([])
  const [loading, setLoading] = useState(true)
  const [selectedWorkshop, setSelectedWorkshop] = useState<string>('')
  const [selectedDevice, setSelectedDevice] = useState<DeviceAssignment | null>(null)
  const [isUnassigning, setIsUnassigning] = useState(false)

  // Assign-to-pit modal state
  const [assignDevice, setAssignDevice] = useState<DeviceAssignment | null>(null)
  const [pitsForAssign, setPitsForAssign] = useState<PitSummary[]>([])
  const [pitsLoading, setPitsLoading] = useState(false)
  const [selectedPitId, setSelectedPitId] = useState('')
  const [isAssigning, setIsAssigning] = useState(false)

  useEffect(() => {
    if (userRole !== 'super_admin') {
      navigate('/dashboard')
    }
  }, [userRole, navigate])

  const fetchData = async () => {
    try {
      const token = localStorage.getItem('ppf_token')
      
      const url = selectedWorkshop
        ? `/api/v1/admin/devices/assignments?workshop_id=${selectedWorkshop}`
        : '/api/v1/admin/devices/assignments'
      
      const res = await fetch(url, {
        headers: { Authorization: `Bearer ${token}` },
      })
      const data = await res.json()
      setAssignments(data.data?.items || [])

      // Fetch workshops for filter
      const wsRes = await fetch('/api/v1/workshops', {
        headers: { Authorization: `Bearer ${token}` },
      })
      const wsData = await wsRes.json()
      setWorkshops(wsData.data?.items || [])
    } catch (error) {
      toast.error('Failed to fetch device assignments')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [selectedWorkshop])

  const handleOpenAssign = async (device: DeviceAssignment) => {
    setAssignDevice(device)
    setSelectedPitId('')
    if (!device.workshop_id) {
      setPitsForAssign([])
      return
    }
    setPitsLoading(true)
    try {
      const pitList = await pitsApi.listPits(device.workshop_id)
      setPitsForAssign(pitList)
    } catch {
      toast.error('Failed to load pits for this workshop')
      setPitsForAssign([])
    } finally {
      setPitsLoading(false)
    }
  }

  const handleAssignToPit = async () => {
    if (!assignDevice || !selectedPitId) {
      toast.error('Please select a pit')
      return
    }
    const pitId = parseInt(selectedPitId)
    const workshopId = assignDevice.workshop_id
    if (!workshopId || !pitId) return

    setIsAssigning(true)
    try {
      await devicesApi.assign(assignDevice.device_id, workshopId, pitId)
      toast.success('Device assigned to pit successfully!')
      setAssignDevice(null)
      setSelectedPitId('')
      fetchData()
    } catch (error: any) {
      toast.error(
        error?.response?.data?.detail?.[0]?.msg ||
        error?.response?.data?.detail ||
        'Failed to assign device to pit'
      )
    } finally {
      setIsAssigning(false)
    }
  }

  const handleUnassign = async () => {
    if (!selectedDevice) return

    setIsUnassigning(true)
    try {
      const token = localStorage.getItem('ppf_token')
      const res = await fetch(
        `/api/v1/admin/devices/${selectedDevice.device_id}/unassign`,
        {
          method: 'POST',
          headers: { Authorization: `Bearer ${token}` },
        }
      )

      if (res.ok) {
        toast.success('Device unassigned successfully')
        setSelectedDevice(null)
        fetchData()
      } else {
        toast.error('Failed to unassign device')
      }
    } catch (error) {
      toast.error('Error unassigning device')
    } finally {
      setIsUnassigning(false)
    }
  }

  if (loading) return <PageSpinner />

  return (
    <div className="p-6 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Device Assignments</h1>
          <p className="text-sm text-gray-500 mt-1">
            View all device → workshop → owner → pit relationships
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

      {/* Filters */}
      <div className="card p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-end">
          <div className="flex-1 min-w-[200px]">
            <Select
              label="Filter by Workshop"
              value={selectedWorkshop}
              onChange={(e) => setSelectedWorkshop(e.target.value)}
              options={[
                { value: '', label: 'All Workshops' },
                ...workshops.map((w) => ({ value: String(w.id), label: w.name })),
              ]}
            />
          </div>
          <div className="text-sm text-gray-500">
            Total: <span className="text-white font-medium">{assignments.length}</span> devices
          </div>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="card p-4">
          <p className="text-sm text-gray-500">Total Assigned</p>
          <p className="text-2xl font-bold text-white">{assignments.length}</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-500">Online</p>
          <p className="text-2xl font-bold text-emerald-400">
            {assignments.filter((a) => a.is_online).length}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-500">Assigned to Pit</p>
          <p className="text-2xl font-bold text-electric-blue">
            {assignments.filter((a) => a.pit_id).length}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-500">Unassigned to Pit</p>
          <p className="text-2xl font-bold text-amber-400">
            {assignments.filter((a) => !a.pit_id).length}
          </p>
        </div>
      </div>

      {/* Assignments Table */}
      {assignments.length === 0 ? (
        <div className="card p-8 text-center">
          <Cpu className="h-12 w-12 text-gray-600 mx-auto mb-4" />
          <p className="text-white font-medium">No device assignments</p>
          <p className="text-sm text-gray-500 mt-2">
            Approved devices will appear here.
          </p>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5 border-b border-white/10">
                <tr>
                  <th className="text-left p-4 text-sm font-medium text-gray-400">Device</th>
                  <th className="text-left p-4 text-sm font-medium text-gray-400">Status</th>
                  <th className="text-left p-4 text-sm font-medium text-gray-400">Workshop</th>
                  <th className="text-left p-4 text-sm font-medium text-gray-400">Owner</th>
                  <th className="text-left p-4 text-sm font-medium text-gray-400">Pit</th>
                  <th className="text-left p-4 text-sm font-medium text-gray-400">Sensors</th>
                  <th className="text-right p-4 text-sm font-medium text-gray-400">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {assignments.map((assignment) => (
                  <tr key={assignment.device_id} className="hover:bg-white/[0.02]">
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <Cpu className="h-4 w-4 text-electric-blue" />
                        <span className="font-mono text-sm text-white">
                          {assignment.device_id}
                        </span>
                      </div>
                      {assignment.license_key && (
                        <p className="text-xs text-gray-500 mt-1">
                          License: {assignment.license_key}
                        </p>
                      )}
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        {assignment.is_online ? (
                          <Badge variant="success">Online</Badge>
                        ) : (
                          <Badge variant="default">Offline</Badge>
                        )}
                        <Badge
                          variant={
                            assignment.device_status === 'active'
                              ? 'success'
                              : assignment.device_status === 'suspended'
                              ? 'danger'
                              : 'warning'
                          }
                        >
                          {assignment.device_status}
                        </Badge>
                      </div>
                      {assignment.last_seen && (
                        <p className="text-xs text-gray-500 mt-1">
                          {new Date(assignment.last_seen).toLocaleString()}
                        </p>
                      )}
                    </td>
                    <td className="p-4">
                      {assignment.workshop_name ? (
                        <div className="flex items-center gap-2">
                          <Building2 className="h-4 w-4 text-gray-500" />
                          <span className="text-sm text-white">
                            {assignment.workshop_name}
                          </span>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-500">-</span>
                      )}
                    </td>
                    <td className="p-4">
                      {assignment.owner_username ? (
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-gray-500" />
                          <span className="text-sm text-white">
                            {assignment.owner_username}
                          </span>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-500">-</span>
                      )}
                    </td>
                    <td className="p-4">
                      {assignment.pit_name ? (
                        <div className="flex items-center gap-2">
                          <MapPin className="h-4 w-4 text-emerald-500" />
                          <span className="text-sm text-white">
                            {assignment.pit_name}
                          </span>
                        </div>
                      ) : (
                        <Badge variant="warning">No Pit</Badge>
                      )}
                    </td>
                    <td className="p-4">
                      <span className="text-sm text-gray-400">
                        {assignment.primary_sensor_code || 'Unknown'}
                        {assignment.air_quality_sensor_code &&
                          ` + ${assignment.air_quality_sensor_code}`}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          size="sm"
                          variant="outline"
                          leftIcon={<MapPin className="h-3 w-3" />}
                          onClick={() => handleOpenAssign(assignment)}
                        >
                          {assignment.pit_id ? 'Change Pit' : 'Assign Pit'}
                        </Button>
                        <Button
                          size="sm"
                          variant="danger"
                          leftIcon={<Unlink className="h-3 w-3" />}
                          onClick={() => setSelectedDevice(assignment)}
                        >
                          Unassign
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ── Assign to Pit Modal ──────────────────────────────────────────────── */}
      <Modal
        isOpen={!!assignDevice}
        onClose={() => { setAssignDevice(null); setSelectedPitId('') }}
        title="Assign Device to Pit"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-400">
            Select a pit in <span className="text-white font-medium">{assignDevice?.workshop_name || 'this workshop'}</span> to assign this device to.
          </p>

          {assignDevice && (
            <div className="bg-black/30 p-3 rounded-lg text-sm space-y-1">
              <p>
                <span className="text-gray-500">Device:</span>{' '}
                <span className="text-white font-mono">{assignDevice.device_id}</span>
              </p>
              <p>
                <span className="text-gray-500">Workshop:</span>{' '}
                <span className="text-white">{assignDevice.workshop_name || '-'}</span>
              </p>
            </div>
          )}

          {pitsLoading ? (
            <p className="text-sm text-gray-400">Loading pits…</p>
          ) : pitsForAssign.length === 0 ? (
            <div className="bg-amber-500/10 border border-amber-500/30 rounded-lg p-3">
              <p className="text-sm text-amber-400">
                No pits found for this workshop. Ask the workshop owner to create pits on their Dashboard first.
              </p>
            </div>
          ) : (
            <div>
              <label className="block text-sm font-medium text-gray-300 mb-1.5">
                Select Pit <span className="text-red-400">*</span>
              </label>
              <select
                value={selectedPitId}
                onChange={(e) => setSelectedPitId(e.target.value)}
                className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white text-sm focus:border-electric-blue focus:ring-1 focus:ring-electric-blue outline-none transition-all"
              >
                <option value="">Choose a pit…</option>
                {pitsForAssign.map((p) => (
                  <option key={p.id} value={String(p.id)}>
                    Pit #{p.pit_number} — {p.name}
                    {p.device ? ' (occupied)' : ''}
                  </option>
                ))}
              </select>
            </div>
          )}

          <div className="flex gap-3 pt-2">
            <Button
              className="flex-1"
              onClick={handleAssignToPit}
              isLoading={isAssigning}
              disabled={!selectedPitId || pitsForAssign.length === 0}
            >
              Assign to Pit
            </Button>
            <Button
              variant="secondary"
              onClick={() => { setAssignDevice(null); setSelectedPitId('') }}
            >
              Cancel
            </Button>
          </div>
        </div>
      </Modal>

      {/* Unassign Modal */}
      <Modal
        isOpen={!!selectedDevice}
        onClose={() => setSelectedDevice(null)}
        title="Unassign Device"
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-400">
            Are you sure you want to unassign this device? It will return to pending status
            and the license key will be revoked.
          </p>

          {selectedDevice && (
            <div className="bg-black/30 p-3 rounded-lg text-sm space-y-1">
              <p>
                <span className="text-gray-500">Device:</span>{' '}
                <span className="text-white font-mono">{selectedDevice.device_id}</span>
              </p>
              <p>
                <span className="text-gray-500">Workshop:</span>{' '}
                <span className="text-white">{selectedDevice.workshop_name || '-'}</span>
              </p>
              <p>
                <span className="text-gray-500">License:</span>{' '}
                <span className="text-white font-mono">{selectedDevice.license_key}</span>
              </p>
            </div>
          )}

          <div className="flex gap-3 pt-4">
            <Button
              variant="danger"
              className="flex-1"
              onClick={handleUnassign}
              isLoading={isUnassigning}
            >
              Unassign Device
            </Button>
            <Button variant="secondary" onClick={() => setSelectedDevice(null)}>
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
