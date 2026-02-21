import { format, formatDistanceToNow, parseISO, differenceInMinutes } from 'date-fns'

// ─── Date & time ──────────────────────────────────────────────────────────────

export function formatDate(iso: string | null | undefined, fmt = 'dd MMM yyyy, HH:mm'): string {
  if (!iso) return '—'
  try {
    return format(parseISO(iso), fmt)
  } catch {
    return '—'
  }
}

export function formatRelative(iso: string | null | undefined): string {
  if (!iso) return '—'
  try {
    return formatDistanceToNow(parseISO(iso), { addSuffix: true })
  } catch {
    return '—'
  }
}

export function formatDurationMinutes(minutes: number | null | undefined): string {
  if (minutes == null) return '—'
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  if (h === 0) return `${m}m`
  if (m === 0) return `${h}h`
  return `${h}h ${m}m`
}

export function getRemainingMinutes(estimatedEnd: string | null | undefined): number | null {
  if (!estimatedEnd) return null
  try {
    const remaining = differenceInMinutes(parseISO(estimatedEnd), new Date())
    return remaining > 0 ? remaining : 0
  } catch {
    return null
  }
}

// ─── Currency ─────────────────────────────────────────────────────────────────

export function formatCurrency(
  amount: number | null | undefined,
  currency = 'INR'
): string {
  if (amount == null) return '—'
  return new Intl.NumberFormat('en-IN', {
    style: 'currency',
    currency,
    maximumFractionDigits: 0,
  }).format(amount)
}

// ─── Sensor values ────────────────────────────────────────────────────────────

export function formatSensorValue(
  value: number | null | undefined,
  decimals = 1
): string {
  if (value == null) return '—'
  return value.toFixed(decimals)
}

// ─── Text ─────────────────────────────────────────────────────────────────────

export function truncate(str: string, maxLen: number): string {
  if (str.length <= maxLen) return str
  return str.slice(0, maxLen) + '…'
}

export function toTitleCase(str: string): string {
  return str.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase())
}
