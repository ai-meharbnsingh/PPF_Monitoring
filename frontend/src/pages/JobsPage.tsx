import { useEffect, useState, useCallback } from 'react'
import { useAppDispatch, useAppSelector } from '@/hooks/useAppDispatch'
import { setJobs, setJobsLoading, setFilters } from '@/store/slices/jobsSlice'
import { jobsApi } from '@/api/jobs'
import { JobCard } from '@/components/jobs/JobCard'
import { JobCreateModal } from '@/components/jobs/JobCreateModal'
import { Pagination } from '@/components/ui/Pagination'
import { Skeleton } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Button } from '@/components/ui/Button'
import { RoleGuard } from '@/components/auth/ProtectedRoute'
import { Plus, Briefcase } from 'lucide-react'
import { usePagination } from '@/hooks/usePagination'
import type { JobStatus } from '@/types/common'
import { clsx } from 'clsx'

const STATUS_TABS: { value: JobStatus | 'all'; label: string }[] = [
  { value: 'all', label: 'All' },
  { value: 'waiting', label: 'Waiting' },
  { value: 'in_progress', label: 'In Progress' },
  { value: 'quality_check', label: 'QC' },
  { value: 'completed', label: 'Done' },
  { value: 'cancelled', label: 'Cancelled' },
]

export default function JobsPage() {
  const dispatch = useAppDispatch()
  const workshopId = useAppSelector((s) => s.auth.user?.workshop_id)
  const { items, pagination, isLoading, filters } = useAppSelector((s) => s.jobs)
  const { page, pageSize, nextPage, prevPage, goToPage } = usePagination(1, 20)
  const [createOpen, setCreateOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<JobStatus | 'all'>('all')

  const loadJobs = useCallback(async () => {
    if (!workshopId) return
    dispatch(setJobsLoading(true))
    try {
      const resp = await jobsApi.list(workshopId, {
        page,
        page_size: pageSize,
        status: activeTab === 'all' ? undefined : activeTab,
      })
      dispatch(
        setJobs({
          items: resp.items,
          pagination: {
            total: resp.total,
            page: resp.page,
            page_size: resp.page_size,
            total_pages: resp.total_pages,
            has_next: resp.has_next,
            has_prev: resp.has_prev,
          },
        }),
      )
    } catch {
      dispatch(setJobsLoading(false))
    }
  }, [workshopId, page, pageSize, activeTab, dispatch])

  useEffect(() => {
    void loadJobs()
  }, [loadJobs])

  const handleTabChange = (tab: JobStatus | 'all') => {
    setActiveTab(tab)
    goToPage(1)
    dispatch(setFilters({ status: tab === 'all' ? null : tab }))
  }

  return (
    <div className="p-6">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <h1 className="text-xl font-bold text-gray-900">Jobs</h1>
        <RoleGuard roles={['owner', 'super_admin', 'staff']}>
          <Button
            size="sm"
            leftIcon={<Plus className="h-4 w-4" />}
            onClick={() => setCreateOpen(true)}
          >
            New Job
          </Button>
        </RoleGuard>
      </div>

      {/* Status tabs */}
      <div className="flex gap-1 mb-5 overflow-x-auto pb-1">
        {STATUS_TABS.map((tab) => (
          <button
            key={tab.value}
            onClick={() => handleTabChange(tab.value)}
            className={clsx(
              'px-3 py-1.5 rounded-lg text-sm font-medium whitespace-nowrap transition-colors',
              activeTab === tab.value
                ? 'bg-blue-600 text-white'
                : 'text-gray-600 hover:bg-gray-100',
            )}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* List */}
      {isLoading && items.length === 0 ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-20" />)}
        </div>
      ) : items.length === 0 ? (
        <EmptyState
          icon={<Briefcase className="h-12 w-12" />}
          title="No jobs found"
          description={
            activeTab === 'all'
              ? 'Create your first job to get started.'
              : `No ${activeTab.replace('_', ' ')} jobs.`
          }
          action={
            <Button
              size="sm"
              leftIcon={<Plus className="h-4 w-4" />}
              onClick={() => setCreateOpen(true)}
            >
              New Job
            </Button>
          }
        />
      ) : (
        <>
          <div className="space-y-3">
            {items.map((job) => (
              <JobCard key={job.id} job={job} />
            ))}
          </div>
          <Pagination
            className="mt-6"
            page={pagination.page}
            totalPages={pagination.total_pages}
            hasNext={pagination.has_next}
            hasPrev={pagination.has_prev}
            onNext={nextPage}
            onPrev={prevPage}
          />
        </>
      )}

      {workshopId && (
        <JobCreateModal
          isOpen={createOpen}
          onClose={() => setCreateOpen(false)}
          workshopId={workshopId}
        />
      )}
    </div>
  )
}
