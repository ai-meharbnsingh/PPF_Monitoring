import type { AlertSeverity, JobStatus, SensorStatus } from '@/types/common'
import type { LatestSensorSummary } from '@/types/sensor'

// ─── Sensor status color system (dark theme) ──────────────────────────────────

export const STATUS_COLORS: Record<
  SensorStatus,
  { bg: string; border: string; text: string; dot: string; ring: string }
> = {
  good: {
    bg:     'bg-emerald-500/10',
    border: 'border-emerald-500/40',
    text:   'text-emerald-400',
    dot:    'bg-emerald-400',
    ring:   'ring-emerald-400/50',
  },
  warning: {
    bg:     'bg-amber-500/10',
    border: 'border-amber-500/40',
    text:   'text-amber-400',
    dot:    'bg-amber-400',
    ring:   'ring-amber-400/50',
  },
  critical: {
    bg:     'bg-red-500/10',
    border: 'border-red-500/40',
    text:   'text-red-400',
    dot:    'bg-red-400',
    ring:   'ring-red-400/50',
  },
  unknown: {
    bg:     'bg-white/5',
    border: 'border-white/15',
    text:   'text-gray-500',
    dot:    'bg-gray-500',
    ring:   'ring-gray-500/30',
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

// ─── Alert severity colors (dark theme) ──────────────────────────────────────

export const SEVERITY_COLORS: Record<
  AlertSeverity,
  { bg: string; text: string; border: string }
> = {
  info: {
    bg:     'bg-electric-blue/10',
    text:   'text-electric-blue',
    border: 'border-electric-blue/30',
  },
  warning: {
    bg:     'bg-amber-500/10',
    text:   'text-amber-400',
    border: 'border-amber-500/30',
  },
  critical: {
    bg:     'bg-red-500/10',
    text:   'text-red-400',
    border: 'border-red-500/30',
  },
}

// ─── Job status colors (dark theme) ──────────────────────────────────────────

export const JOB_STATUS_COLORS: Record<
  JobStatus,
  { bg: string; text: string; dot: string }
> = {
  waiting: {
    bg:   'bg-white/[0.08]',
    text: 'text-gray-400',
    dot:  'bg-gray-500',
  },
  in_progress: {
    bg:   'bg-electric-blue/10',
    text: 'text-electric-blue',
    dot:  'bg-electric-blue',
  },
  quality_check: {
    bg:   'bg-purple-500/10',
    text: 'text-purple-400',
    dot:  'bg-purple-400',
  },
  completed: {
    bg:   'bg-emerald-500/10',
    text: 'text-emerald-400',
    dot:  'bg-emerald-400',
  },
  cancelled: {
    bg:   'bg-red-500/10',
    text: 'text-red-400',
    dot:  'bg-red-400',
  },
}
