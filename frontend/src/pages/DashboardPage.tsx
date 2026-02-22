import { useEffect, useCallback } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useAppDispatch'
import { setPits, setSensorSummaries, setPitsLoading, setPitsError } from '@/store/slices/pitsSlice'
import { pitsApi } from '@/api/pits'
import { sensorsApi } from '@/api/sensors'
import { SensorCard } from '@/components/sensors/SensorCard'
import { PageSpinner, Skeleton } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { LayoutDashboard, RefreshCw } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { formatRelative } from '@/utils/formatters'

export default function DashboardPage() {
  const dispatch = useAppDispatch()
  const workshopId = useAppSelector((s) => s.auth.user?.workshop_id)
  const { pits, sensorMap, isLoading, lastUpdated, error } = useAppSelector((s) => s.pits)

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
    <div className="p-6">
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
        <Button
          variant="outline"
          size="sm"
          onClick={loadData}
          isLoading={isLoading}
          leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
        >
          Refresh
        </Button>
      </div>

      {error && (
        <div className="mb-4 p-3 rounded-lg text-sm text-red-400 border border-red-500/30 bg-red-500/10">
          {error}
        </div>
      )}

      {pits.length === 0 ? (
        <EmptyState
          icon={<LayoutDashboard className="h-12 w-12 text-electric-blue/50" />}
          title="No pits found"
          description="Add pits to your workshop to start monitoring."
        />
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-3 gap-4">
          {pits.map((pit) => (
            <SensorCard key={pit.id} pit={pit} sensors={sensorMap[pit.id]} />
          ))}
        </div>
      )}
    </div>
  )
}
