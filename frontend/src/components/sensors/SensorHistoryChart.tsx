import { useEffect, useState, useCallback } from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts'
import { sensorsApi } from '@/api/sensors'
import type { SensorReadingResponse } from '@/types/sensor'
import { Spinner } from '@/components/ui/Spinner'
import { format, parseISO, subHours } from 'date-fns'
import { clsx } from 'clsx'

interface SensorHistoryChartProps {
  pitId: number
  className?: string
}

type Range = '1h' | '6h' | '24h' | '7d'

const RANGE_OPTIONS: { value: Range; label: string; hours: number }[] = [
  { value: '1h', label: '1h', hours: 1 },
  { value: '6h', label: '6h', hours: 6 },
  { value: '24h', label: '24h', hours: 24 },
  { value: '7d', label: '7d', hours: 168 },
]

const formatXAxis = (iso: string, hours: number) => {
  try {
    if (hours <= 6) return format(parseISO(iso), 'HH:mm')
    if (hours <= 24) return format(parseISO(iso), 'HH:mm')
    return format(parseISO(iso), 'dd MMM HH:mm')
  } catch {
    return ''
  }
}

interface ChartDataPoint {
  time: string
  temp?: number
  humidity?: number
  pm25?: number
  pm10?: number
}

export function SensorHistoryChart({ pitId, className }: SensorHistoryChartProps) {
  const [range, setRange] = useState<Range>('24h')
  const [data, setData] = useState<ChartDataPoint[]>([])
  const [loading, setLoading] = useState(false)

  const selectedRange = RANGE_OPTIONS.find((r) => r.value === range)!

  const loadHistory = useCallback(async () => {
    setLoading(true)
    try {
      const from = subHours(new Date(), selectedRange.hours).toISOString()
      const resp = await sensorsApi.history(pitId, {
        page: 1,
        page_size: 200,
        from_dt: from,
      })
      const points: ChartDataPoint[] = resp.items.map((r: SensorReadingResponse) => ({
        time: r.device_timestamp,
        temp: r.temperature ?? undefined,
        humidity: r.humidity ?? undefined,
        pm25: r.pm25 ?? undefined,
        pm10: r.pm10 ?? undefined,
      }))
      setData(points.reverse()) // chronological order
    } catch {
      setData([])
    } finally {
      setLoading(false)
    }
  }, [pitId, selectedRange.hours])

  useEffect(() => {
    void loadHistory()
  }, [loadHistory])

  return (
    <div className={className}>
      {/* Range tabs */}
      <div className="flex gap-1 mb-4">
        {RANGE_OPTIONS.map((r) => (
          <button
            key={r.value}
            onClick={() => setRange(r.value)}
            className={clsx(
              'px-3 py-1 rounded-lg text-xs font-medium transition-colors',
              range === r.value
                ? 'bg-blue-600 text-white'
                : 'text-gray-500 hover:bg-gray-100',
            )}
          >
            {r.label}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex items-center justify-center h-48">
          <Spinner />
        </div>
      ) : data.length === 0 ? (
        <div className="flex items-center justify-center h-48 text-sm text-gray-400">
          No data for this period
        </div>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <LineChart data={data} margin={{ top: 5, right: 10, left: -10, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
            <XAxis
              dataKey="time"
              tickFormatter={(v: string) => formatXAxis(v, selectedRange.hours)}
              tick={{ fontSize: 10 }}
              stroke="#d1d5db"
            />
            <YAxis tick={{ fontSize: 10 }} stroke="#d1d5db" />
            <Tooltip
              labelFormatter={(label: string) => format(parseISO(label), 'dd MMM HH:mm')}
              contentStyle={{ fontSize: 12, borderRadius: 8, border: '1px solid #e5e7eb' }}
            />
            <Legend wrapperStyle={{ fontSize: 11 }} />
            <Line
              type="monotone"
              dataKey="temp"
              name="Temp (°C)"
              stroke="#ef4444"
              dot={false}
              strokeWidth={1.5}
            />
            <Line
              type="monotone"
              dataKey="humidity"
              name="Humidity (%)"
              stroke="#3b82f6"
              dot={false}
              strokeWidth={1.5}
            />
            <Line
              type="monotone"
              dataKey="pm25"
              name="PM2.5 (μg/m³)"
              stroke="#f97316"
              dot={false}
              strokeWidth={1.5}
            />
            <Line
              type="monotone"
              dataKey="pm10"
              name="PM10 (μg/m³)"
              stroke="#8b5cf6"
              dot={false}
              strokeWidth={1.5}
            />
          </LineChart>
        </ResponsiveContainer>
      )}
    </div>
  )
}
