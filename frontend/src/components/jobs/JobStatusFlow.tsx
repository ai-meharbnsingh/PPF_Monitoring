import { clsx } from 'clsx'
import { Check } from 'lucide-react'
import type { JobStatus } from '@/types/common'

const FLOW_STEPS: { status: JobStatus; label: string }[] = [
  { status: 'waiting', label: 'Waiting' },
  { status: 'in_progress', label: 'In Progress' },
  { status: 'quality_check', label: 'QC' },
  { status: 'completed', label: 'Done' },
]

const STEP_ORDER: Record<JobStatus, number> = {
  waiting: 0,
  in_progress: 1,
  quality_check: 2,
  completed: 3,
  cancelled: -1,
}

interface JobStatusFlowProps {
  status: JobStatus
  compact?: boolean
  theme?: 'light' | 'dark'
}

export function JobStatusFlow({ status, compact = false, theme = 'light' }: JobStatusFlowProps) {
  if (status === 'cancelled') {
    return (
      <div className="flex items-center gap-2">
        <span className="px-3 py-1 rounded-full bg-red-100 text-red-700 text-xs font-semibold">
          Cancelled
        </span>
      </div>
    )
  }

  const currentIndex = STEP_ORDER[status]

  return (
    <div className={clsx('flex items-center', compact ? 'gap-1' : 'gap-2')}>
      {FLOW_STEPS.map((step, idx) => {
        const isCompleted = idx < currentIndex
        const isCurrent = idx === currentIndex
        const isPending = idx > currentIndex

        const activeNodeBg = theme === 'dark' ? 'bg-electric-blue ring-4 ring-electric-blue/20' : 'bg-blue-600 ring-4 ring-blue-100'
        const completedNodeBg = theme === 'dark' ? 'bg-emerald-500' : 'bg-green-500'
        const pendingNodeBg = theme === 'dark' ? 'bg-white/10' : 'bg-gray-200'

        const activeText = theme === 'dark' ? 'text-electric-blue' : 'text-blue-700'
        const completedText = theme === 'dark' ? 'text-emerald-400' : 'text-green-600'
        const pendingText = theme === 'dark' ? 'text-gray-500' : 'text-gray-400'

        const activeLineBg = theme === 'dark' ? 'bg-emerald-500' : 'bg-green-400'
        const pendingLineBg = theme === 'dark' ? 'bg-white/10' : 'bg-gray-200'

        return (
          <div key={step.status} className="flex items-center">
            {/* Step node */}
            <div className="flex flex-col items-center">
              <div
                className={clsx(
                  'rounded-full flex items-center justify-center transition-colors',
                  compact ? 'w-6 h-6' : 'w-8 h-8',
                  isCompleted && completedNodeBg,
                  isCurrent && activeNodeBg,
                  isPending && pendingNodeBg,
                )}
              >
                {isCompleted ? (
                  <Check className={clsx(theme === 'dark' ? 'text-matte-black' : 'text-white', compact ? 'h-3 w-3' : 'h-4 w-4')} />
                ) : (
                  <span
                    className={clsx(
                      'font-semibold',
                      compact ? 'text-[10px]' : 'text-xs',
                      isCurrent && (theme === 'dark' ? 'text-black' : 'text-white'),
                      !isCurrent && (theme === 'dark' ? 'text-gray-500' : 'text-gray-400'),
                    )}
                  >
                    {idx + 1}
                  </span>
                )}
              </div>
              {!compact && (
                <span
                  className={clsx(
                    'text-[10px] mt-2 font-medium text-center uppercase tracking-wider',
                    isCurrent ? activeText : isCompleted ? completedText : pendingText,
                  )}
                >
                  {step.label}
                </span>
              )}
            </div>

            {/* Connector line */}
            {idx < FLOW_STEPS.length - 1 && (
              <div
                className={clsx(
                  'h-0.5 transition-colors',
                  compact ? 'w-4' : 'w-8',
                  idx < currentIndex ? activeLineBg : pendingLineBg,
                  { 'mt-[-16px]': !compact } // visually offset line to align with node, not text
                )}
              />
            )}
          </div>
        )
      })}
    </div>
  )
}
