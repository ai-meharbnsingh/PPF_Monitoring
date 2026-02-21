import { useEffect, useState } from 'react'
import { X, CheckCheck } from 'lucide-react'
import { useAppDispatch, useAppSelector } from '@/hooks/useAppDispatch'
import { setPanelOpen, setAlerts, acknowledgeAlert, acknowledgeAll as acknowledgeAllAction } from '@/store/slices/alertsSlice'
import { alertsApi } from '@/api/alerts'
import { AlertItem } from './AlertItem'
import { Button } from '@/components/ui/Button'
import { Spinner } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Bell } from 'lucide-react'
import { clsx } from 'clsx'
import toast from 'react-hot-toast'

export function AlertPanel() {
  const dispatch = useAppDispatch()
  const { isPanelOpen, items, isLoading } = useAppSelector((s) => s.alerts)
  const workshopId = useAppSelector((s) => s.auth.user?.workshop_id)
  const [acknowledging, setAcknowledging] = useState<number | null>(null)

  useEffect(() => {
    if (isPanelOpen && workshopId) {
      dispatch({ type: 'alerts/setLoading', payload: true })
      alertsApi
        .list(workshopId, { page: 1, page_size: 50 })
        .then((resp) => {
          dispatch(
            setAlerts({
              items: resp.items,
              pagination: {
                total: resp.total,
                page: resp.page,
                total_pages: resp.total_pages,
                has_next: resp.has_next,
              },
            }),
          )
        })
        .catch(() => {})
    }
  }, [isPanelOpen, workshopId, dispatch])

  const handleAcknowledge = async (id: number) => {
    setAcknowledging(id)
    try {
      await alertsApi.acknowledge(id)
      dispatch(acknowledgeAlert(id))
      toast.success('Alert acknowledged')
    } catch {
      toast.error('Failed to acknowledge')
    } finally {
      setAcknowledging(null)
    }
  }

  const handleAcknowledgeAll = async () => {
    if (!workshopId) return
    try {
      await alertsApi.acknowledgeAll(workshopId)
      dispatch(acknowledgeAllAction())
      toast.success('All alerts acknowledged')
    } catch {
      toast.error('Failed to acknowledge all')
    }
  }

  const unacknowledged = items.filter((a) => !a.is_acknowledged)

  return (
    <>
      {/* Backdrop */}
      {isPanelOpen && (
        <div
          className="fixed inset-0 z-40 bg-black/20"
          onClick={() => dispatch(setPanelOpen(false))}
        />
      )}

      {/* Panel */}
      <div
        className={clsx(
          'fixed top-0 right-0 z-50 h-screen w-full max-w-sm bg-white shadow-2xl',
          'flex flex-col transition-transform duration-300 ease-in-out border-l border-gray-200',
          isPanelOpen ? 'translate-x-0' : 'translate-x-full',
        )}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-4 border-b border-gray-100">
          <h2 className="font-semibold text-gray-900">Alerts</h2>
          <div className="flex items-center gap-2">
            {unacknowledged.length > 0 && (
              <Button size="sm" variant="ghost" onClick={handleAcknowledgeAll}>
                <CheckCheck className="h-3.5 w-3.5" />
                Ack All
              </Button>
            )}
            <button
              onClick={() => dispatch(setPanelOpen(false))}
              className="p-1.5 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100"
            >
              <X className="h-4 w-4" />
            </button>
          </div>
        </div>

        {/* Body */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {isLoading ? (
            <Spinner className="py-8" />
          ) : items.length === 0 ? (
            <EmptyState
              icon={<Bell className="h-10 w-10" />}
              title="No alerts"
              description="You're all clear!"
            />
          ) : (
            items.map((alert) => (
              <AlertItem
                key={alert.id}
                alert={alert}
                onAcknowledge={handleAcknowledge}
                isAcknowledging={acknowledging === alert.id}
              />
            ))
          )}
        </div>
      </div>
    </>
  )
}
