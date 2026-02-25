import { useEffect, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '@/hooks/useAppDispatch'
import { setAlerts, setAlertsLoading, acknowledgeAlert } from '@/store/slices/alertsSlice'
import { alertsApi } from '@/api/alerts'
import { AlertItem } from '@/components/alerts/AlertItem'
import { Pagination } from '@/components/ui/Pagination'
import { Skeleton } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { RoleGuard } from '@/components/auth/ProtectedRoute'
import { Bell, Settings } from 'lucide-react'
import { usePagination } from '@/hooks/usePagination'
import { useState } from 'react'
import toast from 'react-hot-toast'

export default function AlertsPage() {
  const dispatch = useAppDispatch()
  const workshopId = useAppSelector((s) => s.auth.user?.workshop_id)
  const { items, pagination, isLoading } = useAppSelector((s) => s.alerts)
  const { page, pageSize, nextPage, prevPage } = usePagination(1, 30)
  const [acknowledging, setAcknowledging] = useState<number | null>(null)

  const loadAlerts = useCallback(async () => {
    if (!workshopId) return
    dispatch(setAlertsLoading(true))
    try {
      const resp = await alertsApi.list(workshopId, { page, page_size: pageSize })
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
    } catch {
      dispatch(setAlertsLoading(false))
    }
  }, [workshopId, page, pageSize, dispatch])

  useEffect(() => {
    void loadAlerts()
  }, [loadAlerts])

  const handleAcknowledge = async (id: number) => {
    setAcknowledging(id)
    try {
      await alertsApi.acknowledge(id)
      dispatch(acknowledgeAlert(id))
      toast.success('Alert acknowledged')
    } catch {
      toast.error('Failed')
    } finally {
      setAcknowledging(null)
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Alerts</h1>
        <RoleGuard roles={['owner', 'super_admin']}>
          <Link to="/admin/alerts/config">
            <Button variant="secondary" size="sm" leftIcon={<Settings className="h-4 w-4" />}>
              Configure
            </Button>
          </Link>
        </RoleGuard>
      </div>

      {isLoading && items.length === 0 ? (
        <div className="space-y-3">
          {[1, 2, 3, 4].map((i) => <Skeleton key={i} className="h-20" />)}
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={<Bell className="h-12 w-12" />}
          title="No alerts"
          description="All clear! No alerts have been triggered."
        />
      ) : (
        <>
          <div className="space-y-2">
            {items.map((alert) => (
              <AlertItem
                key={alert.id}
                alert={alert}
                onAcknowledge={handleAcknowledge}
                isAcknowledging={acknowledging === alert.id}
              />
            ))}
          </div>
          <Pagination
            className="mt-6"
            page={pagination.page}
            totalPages={pagination.total_pages}
            hasNext={pagination.has_next}
            hasPrev={page > 1}
            onNext={nextPage}
            onPrev={prevPage}
          />
        </>
      )}
    </div>
  )
}
