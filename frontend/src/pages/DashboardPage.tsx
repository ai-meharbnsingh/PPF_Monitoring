import { useEffect, useCallback, useState } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useAppDispatch'
import { setPits, setSensorSummaries, setPitsLoading, setPitsError } from '@/store/slices/pitsSlice'
import { pitsApi } from '@/api/pits'
import { sensorsApi } from '@/api/sensors'
import { SensorCard } from '@/components/sensors/SensorCard'
import { Skeleton } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Modal } from '@/components/ui/Modal'
import { LayoutDashboard, RefreshCw, Plus } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { formatRelative } from '@/utils/formatters'
import toast from 'react-hot-toast'

export default function DashboardPage() {
  const dispatch = useAppDispatch()
  const workshopId = useAppSelector((s) => s.auth.user?.workshop_id)
  const { pits, sensorMap, isLoading, lastUpdated, error } = useAppSelector((s) => s.pits)

  // ── Create Pit modal ───────────────────────────────────────────────────────
  const [addPitOpen, setAddPitOpen] = useState(false)
  const [pitName, setPitName] = useState('')
  const [pitNumber, setPitNumber] = useState('')
  const [pitDescription, setPitDescription] = useState('')
  const [creating, setCreating] = useState(false)

  const loadData = useCallback(async () => {
    if (!workshopId) return
    dispatch(setPitsLoading(true))
    try {
      const [pitList, sensorList] = await Promise.all([
        pitsApi.listPits(workshopId),
        sensorsApi.latestForWorkshop(workshopId),
      ])
      dispatch(setPits(pitList))
      dispatch(setSensorSummaries(sensorList))
    } catch {
      dispatch(setPitsError('Failed to load dashboard data'))
    }
  }, [workshopId, dispatch])

  // Load on mount
  useEffect(() => {
    void loadData()
  }, [loadData])

  // Poll every 30 seconds as fallback (WS handles real-time updates)
  useEffect(() => {
    const id = setInterval(() => void loadData(), 30_000)
    return () => clearInterval(id)
  }, [loadData])

  const handleCreatePit = async () => {
    if (!workshopId) return
    const name = pitName.trim()
    const num = parseInt(pitNumber)
    if (!name) { toast.error('Pit name is required'); return }
    if (!num || num < 1) { toast.error('Pit number must be a positive integer'); return }
    setCreating(true)
    try {
      await pitsApi.createPit(workshopId, {
        pit_number: num,
        name,
        description: pitDescription.trim() || undefined,
      })
      toast.success(`Pit "${name}" created!`)
      setAddPitOpen(false)
      setPitName('')
      setPitNumber('')
      setPitDescription('')
      void loadData()
    } catch (err: any) {
      const detail =
        err?.response?.data?.detail?.[0]?.msg ||
        err?.response?.data?.detail ||
        'Failed to create pit'
      toast.error(detail)
    } finally {
      setCreating(false)
    }
  }

  const handleModalClose = () => {
    setAddPitOpen(false)
    setPitName('')
    setPitNumber('')
    setPitDescription('')
  }

  if (isLoading && pits.length === 0) {
    return (
      <div className="p-6">
        <Skeleton className="h-7 w-48 mb-6 bg-white/5" />
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {[1, 2, 3].map((i) => (
            <Skeleton key={i} className="h-56 bg-white/5" />
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="p-4 sm:p-6 overflow-hidden">
      {/* Page header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-xl font-bold text-white tracking-wide">Dashboard</h1>
          {lastUpdated && (
            <p className="text-xs text-gray-500 mt-0.5">
              Live · Last polled {formatRelative(lastUpdated)}
            </p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            isLoading={isLoading}
            leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
          >
            Refresh
          </Button>
          <Button
            size="sm"
            leftIcon={<Plus className="h-3.5 w-3.5" />}
            onClick={() => setAddPitOpen(true)}
          >
            Add Pit
          </Button>
        </div>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg text-sm text-red-400 border border-red-500/30 bg-red-500/10">
          {error}
        </div>
      )}

      {pits.length === 0 ? (
        <EmptyState
          icon={<LayoutDashboard className="h-12 w-12 text-electric-blue/50" />}
          title="No pits yet"
          description="Create your first pit (work bay) to start monitoring sensor data."
          action={
            <Button
              size="sm"
              leftIcon={<Plus className="h-4 w-4" />}
              onClick={() => setAddPitOpen(true)}
            >
              Add Pit
            </Button>
          }
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {pits.map((pit) => (
            <SensorCard key={pit.id} pit={pit} sensors={sensorMap[pit.id]} />
          ))}
        </div>
      )}

      {/* ── Create Pit Modal ────────────────────────────────────────────────── */}
      <Modal isOpen={addPitOpen} onClose={handleModalClose} title="Add New Pit">
        <div className="space-y-4">
          <p className="text-sm text-gray-400">
            A pit is a work bay in your workshop. Each pit can have one sensor device assigned for monitoring.
          </p>

          {/* Pit Number */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              Pit Number <span className="text-red-400">*</span>
            </label>
            <input
              type="number"
              min={1}
              value={pitNumber}
              onChange={(e) => setPitNumber(e.target.value)}
              placeholder={`e.g. ${(pits.length + 1)}`}
              className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-600 focus:border-electric-blue focus:ring-1 focus:ring-electric-blue outline-none transition-all"
            />
            <p className="text-xs text-gray-600 mt-1">Unique number for this bay</p>
          </div>

          {/* Pit Name */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              Pit Name <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={pitName}
              onChange={(e) => setPitName(e.target.value)}
              placeholder="e.g. Bay A, Engine Bay 1"
              className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-600 focus:border-electric-blue focus:ring-1 focus:ring-electric-blue outline-none transition-all"
              onKeyDown={(e) => e.key === 'Enter' && void handleCreatePit()}
            />
          </div>

          {/* Description (optional) */}
          <div>
            <label className="block text-sm font-medium text-gray-300 mb-1.5">
              Description <span className="text-gray-600 font-normal">(optional)</span>
            </label>
            <input
              type="text"
              value={pitDescription}
              onChange={(e) => setPitDescription(e.target.value)}
              placeholder="e.g. North side of workshop"
              className="w-full bg-black/40 border border-white/10 rounded-lg px-3 py-2 text-white text-sm placeholder-gray-600 focus:border-electric-blue focus:ring-1 focus:ring-electric-blue outline-none transition-all"
            />
          </div>

          <div className="flex gap-3 pt-2">
            <Button className="flex-1" onClick={handleCreatePit} isLoading={creating}>
              Create Pit
            </Button>
            <Button variant="secondary" onClick={handleModalClose}>
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
