import type { AlertSeverity, JobStatus, SensorStatus } from '@/types/common'
import type { LatestSensorSummary } from '@/types/sensor'

// ─── Sensor status color system ───────────────────────────────────────────────

export const STATUS_COLORS: Record<
  SensorStatus,
  { bg: string; border: string; text: string; dot: string; ring: string }
> = {
  good: {
    bg: 'bg-emerald-50',
    border: 'border-emerald-400',
    text: 'text-emerald-700',
    dot: 'bg-emerald-500',
    ring: 'ring-emerald-400',
  },
  warning: {
    bg: 'bg-amber-50',
    border: 'border-amber-400',
    text: 'text-amber-700',
    dot: 'bg-amber-500',
    ring: 'ring-amber-400',
  },
  critical: {
    bg: 'bg-red-50',
    border: 'border-red-500',
    text: 'text-red-700',
    dot: 'bg-red-600',
    ring: 'ring-red-500',
  },
  unknown: {
    bg: 'bg-gray-50',
    border: 'border-gray-300',
    text: 'text-gray-500',
    dot: 'bg-gray-400',
    ring: 'ring-gray-300',
  },
}

const STATUS_ORDER: SensorStatus[] = ['critical', 'warning', 'good', 'unknown']

/** Returns the worst sensor status across all metrics for a pit card */
export function getWorstStatus(summary: LatestSensorSummary): SensorStatus {
  const statuses: SensorStatus[] = [
    summary.temp_status,
    summary.humidity_status,
    summary.pm25_status,
    summary.pm10_status,
    summary.iaq_status,
  ]
  return statuses.reduce((worst, s) => {
    return STATUS_ORDER.indexOf(s) < STATUS_ORDER.indexOf(worst) ? s : worst
  }, 'unknown' as SensorStatus)
}

// ─── Alert severity colors ────────────────────────────────────────────────────

export const SEVERITY_COLORS: Record<
  AlertSeverity,
  { bg: string; text: string; border: string }
> = {
  info: {
    bg: 'bg-blue-100',
    text: 'text-blue-800',
    border: 'border-blue-300',
  },
  warning: {
    bg: 'bg-amber-100',
    text: 'text-amber-800',
    border: 'border-amber-300',
  },
  critical: {
    bg: 'bg-red-100',
    text: 'text-red-800',
    border: 'border-red-300',
  },
}

// ─── Job status colors ────────────────────────────────────────────────────────

export const JOB_STATUS_COLORS: Record<
  JobStatus,
  { bg: string; text: string; dot: string }
> = {
  waiting: {
    bg: 'bg-slate-100',
    text: 'text-slate-700',
    dot: 'bg-slate-500',
  },
  in_progress: {
    bg: 'bg-blue-100',
    text: 'text-blue-800',
    dot: 'bg-blue-500',
  },
  quality_check: {
    bg: 'bg-purple-100',
    text: 'text-purple-800',
    dot: 'bg-purple-500',
  },
  completed: {
    bg: 'bg-green-100',
    text: 'text-green-800',
    dot: 'bg-green-500',
  },
  cancelled: {
    bg: 'bg-red-100',
    text: 'text-red-700',
    dot: 'bg-red-500',
  },
}
