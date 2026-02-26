import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useParams, useNavigate } from 'react-router-dom'
import { pitsApi, type PitAlertConfigResponse, type PitAlertConfigUpdate } from '@/api/pits'
import { sensorsApi } from '@/api/sensors'
import { useAppSelector } from '@/hooks/useAppDispatch'
import type { PitSummary } from '@/types/pit'
import type { LatestSensorSummary } from '@/types/sensor'
import { SensorTile } from '@/components/sensors/SensorTile'
import { SensorHistoryChart } from '@/components/sensors/SensorHistoryChart'
import { StreamTokenLoader } from '@/components/video/StreamTokenLoader'
import { PageSpinner } from '@/components/ui/Spinner'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { STATUS_COLORS, getWorstStatus } from '@/utils/sensorColors'
import { formatRelative } from '@/utils/formatters'
import { clsx } from 'clsx'
import {
  ArrowLeft,
  TrendingUp,
  Thermometer,
  Droplets,
  Wind,
  Gauge,
  BarChart3,
  Wifi,
  WifiOff,
  Settings,
  ChevronDown,
  ChevronUp,
} from 'lucide-react'
import toast from 'react-hot-toast'

const VIDEO_ROLES = ['owner', 'super_admin', 'staff'] as const

const THRESHOLD_FIELDS: { key: string; label: string; unit: string; step: string }[] = [
  { key: 'temp_min', label: 'Temp Min', unit: '°C', step: '0.1' },
  { key: 'temp_max', label: 'Temp Max', unit: '°C', step: '0.1' },
  { key: 'humidity_max', label: 'Humidity Max', unit: '%', step: '0.1' },
  { key: 'pm25_warning', label: 'PM2.5 Warning', unit: 'μg/m³', step: '0.1' },
  { key: 'pm25_critical', label: 'PM2.5 Critical', unit: 'μg/m³', step: '0.1' },
  { key: 'pm10_warning', label: 'PM10 Warning', unit: 'μg/m³', step: '0.1' },
  { key: 'pm10_critical', label: 'PM10 Critical', unit: 'μg/m³', step: '0.1' },
  { key: 'iaq_warning', label: 'IAQ Warning', unit: '', step: '1' },
  { key: 'iaq_critical', label: 'IAQ Critical', unit: '', step: '1' },
  { key: 'device_offline_threshold_seconds', label: 'Offline Threshold', unit: 's', step: '1' },
]

function SourceBadge({ source }: { source: string }) {
  const colors =
    source === 'pit'
      ? 'bg-electric-blue/10 text-electric-blue border-electric-blue/30'
      : source === 'workshop'
        ? 'bg-amber-500/10 text-amber-400 border-amber-500/30'
        : 'bg-gray-500/10 text-gray-500 border-gray-500/30'
  return (
    <span className={`text-[9px] px-1.5 py-0.5 rounded border font-mono uppercase ${colors}`}>
      {source}
    </span>
  )
}

function PitAlertConfigPanel({
  pitId,
  alertCfg,
  alertOpen,
  onToggle,
  onSaved,
}: {
  pitId: number
  alertCfg: PitAlertConfigResponse | null
  alertOpen: boolean
  onToggle: () => void
  onSaved: (cfg: PitAlertConfigResponse) => void
}) {
  const { register, handleSubmit, reset, formState: { isSubmitting } } = useForm<PitAlertConfigUpdate>()
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    if (alertCfg && !loaded) {
      // Pre-fill with current pit override values (null means inherit)
      const values: Record<string, number | null> = {}
      for (const f of THRESHOLD_FIELDS) {
        const src = (alertCfg as unknown as Record<string, unknown>)[`${f.key}_source`]
        values[f.key] = src === 'pit' ? (alertCfg as unknown as Record<string, unknown>)[f.key] as number : null
      }
      reset(values as unknown as PitAlertConfigUpdate)
      setLoaded(true)
    }
  }, [alertCfg, reset, loaded])

  const onSubmit = async (data: PitAlertConfigUpdate) => {
    try {
      // Convert empty strings to null for clearing overrides
      const cleaned: Record<string, number | null> = {}
      for (const f of THRESHOLD_FIELDS) {
        const v = (data as Record<string, unknown>)[f.key]
        cleaned[f.key] = v === '' || v == null ? null : Number(v)
      }
      await pitsApi.updateAlertConfig(pitId, cleaned as unknown as PitAlertConfigUpdate)
      toast.success('Pit thresholds saved')
      // Reload config to update source badges
      const fresh = await pitsApi.getAlertConfig(pitId)
      onSaved(fresh)
      setLoaded(false) // re-sync form
    } catch {
      toast.error('Failed to save thresholds')
    }
  }

  return (
    <div className="card overflow-hidden">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-white/[0.03] transition-colors"
      >
        <div className="flex items-center gap-2">
          <Settings className="h-4 w-4 text-champagne-gold/70" />
          <span className="text-sm font-semibold text-white">Alert Thresholds</span>
          <span className="text-[10px] text-gray-600">per-pit overrides</span>
        </div>
        {alertOpen ? (
          <ChevronUp className="h-4 w-4 text-gray-500" />
        ) : (
          <ChevronDown className="h-4 w-4 text-gray-500" />
        )}
      </button>

      {alertOpen && alertCfg && (
        <form onSubmit={handleSubmit(onSubmit)} className="px-4 pb-4 pt-1">
          <p className="text-[10px] text-gray-600 mb-3">
            Empty fields inherit from workshop config. Set a value to override for this pit only.
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {THRESHOLD_FIELDS.map((f) => (
              <div key={f.key} className="flex items-end gap-2">
                <div className="flex-1">
                  <Input
                    label={`${f.label} ${f.unit ? `(${f.unit})` : ''}`}
                    type="number"
                    step={f.step}
                    placeholder={String((alertCfg as unknown as Record<string, unknown>)[f.key])}
                    {...register(f.key as keyof PitAlertConfigUpdate, { setValueAs: (v: string) => v === '' ? null : Number(v) })}
                  />
                </div>
                <div className="pb-1">
                  <SourceBadge source={(alertCfg as unknown as Record<string, unknown>)[`${f.key}_source`] as string} />
                </div>
              </div>
            ))}
          </div>
          <div className="flex justify-end mt-4">
            <Button type="submit" size="sm" isLoading={isSubmitting}>
              Save Overrides
            </Button>
          </div>
        </form>
      )}
    </div>
  )
}

function CameraTimestamp({ pitNumber, pitName }: { pitNumber: number; pitName: string }) {
  const [now, setNow] = useState(new Date())
  useEffect(() => {
    const t = setInterval(() => setNow(new Date()), 1000)
    return () => clearInterval(t)
  }, [])
  const dateStr = now.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }).toUpperCase()
  const timeStr = now.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit', hour12: false })
  return (
    <div className="absolute bottom-4 left-4 z-20 pointer-events-none space-y-0.5">
      <p className="text-[9px] font-mono text-gray-500 uppercase tracking-widest">
        CAM_{String(pitNumber).padStart(2, '0')}_BAY · {pitName.toUpperCase()}
      </p>
      <p className="text-[9px] font-mono text-gray-500 uppercase">
        {dateStr} {'  '} {timeStr}
        {'  '}
        <span className="text-red-400 font-bold">● LIVE</span>
      </p>
    </div>
  )
}

export default function PitDetailPage() {
  const { pitId } = useParams<{ pitId: string }>()
  const navigate = useNavigate()
  const userRole = useAppSelector((s) => s.auth.user?.role)
  const [pit, setPit] = useState<PitSummary | null>(null)
  const [sensors, setSensors] = useState<LatestSensorSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [alertCfg, setAlertCfg] = useState<PitAlertConfigResponse | null>(null)
  const [alertOpen, setAlertOpen] = useState(false)
  const isOwnerOrAdmin = userRole === 'owner' || userRole === 'super_admin'

  const canViewVideo =
    userRole != null && (VIDEO_ROLES as readonly string[]).includes(userRole)

  // Initial load
  useEffect(() => {
    if (!pitId) return
    const id = Number(pitId)
    setLoading(true)
    Promise.all([pitsApi.getPit(id), sensorsApi.latestForPit(id)])
      .then(([pitData, sensorData]) => {
        setPit(pitData)
        setSensors(sensorData)
      })
      .catch(() => { })
      .finally(() => setLoading(false))
  }, [pitId])

  // Poll sensor data every 15 s so overlay values stay current
  useEffect(() => {
    if (!pitId) return
    const id = Number(pitId)
    const timer = setInterval(() => {
      sensorsApi.latestForPit(id).then(setSensors).catch(() => { })
    }, 15_000)
    return () => clearInterval(timer)
  }, [pitId])

  if (loading) return <PageSpinner />
  if (!pit) return null

  const isOnline = sensors?.is_device_online ?? false
  const worstStatus = sensors ? getWorstStatus(sensors) : 'unknown'
  const colors = STATUS_COLORS[worstStatus]

  // Shared glass-card style for sensor overlays on video
  const overlayCard =
    'flex items-center gap-3 px-3.5 py-2.5 rounded-xl min-w-[165px]'
  const overlayCardStyle = {
    background: 'rgba(8,8,8,0.80)',
    backdropFilter: 'blur(16px)',
    WebkitBackdropFilter: 'blur(16px)',
    border: '1px solid rgba(255,255,255,0.09)',
  }

  return (
    <div className="p-6 min-h-screen">
      {/* ── Header ───────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(-1)}
            className="flex items-center gap-1.5 text-sm text-gray-400 hover:text-white transition-colors"
          >
            <ArrowLeft className="h-4 w-4" />
            Back
          </button>
          <div className="h-4 w-px bg-white/15" />
          <div>
            <h1 className="text-xl font-bold text-white">{pit.name}</h1>
            <p className="text-xs text-gray-500 mt-0.5">Pit #{pit.pit_number}</p>
          </div>
        </div>

        {/* Online / LIVE badge */}
        <div className="flex items-center gap-3">
          {isOnline ? (
            <>
              <span className="flex items-center gap-1.5 text-xs text-emerald-400 font-medium">
                <Wifi className="h-3.5 w-3.5" />
                Device Live
              </span>
              <div className="flex items-center gap-1.5 px-3 py-1.5 bg-red-500/10 border border-red-500/30 rounded-full">
                <span className="h-1.5 w-1.5 rounded-full bg-red-500 animate-pulse" />
                <span className="text-[10px] text-red-400 font-mono font-semibold tracking-widest">
                  LIVE
                </span>
              </div>
            </>
          ) : (
            <span className="flex items-center gap-1.5 text-xs text-gray-500">
              <WifiOff className="h-3.5 w-3.5" />
              Device Offline
            </span>
          )}
        </div>
      </div>

      {/* ── Main Grid ────────────────────────────────────────────────────── */}
      <div
        className={clsx(
          'grid grid-cols-1 gap-6',
          canViewVideo && 'lg:grid-cols-3',
        )}
      >
        {/* LEFT: Live readings + History chart ─────────────────────── */}
        <div className="space-y-5">
          {/* Live readings card */}
          <div className={clsx('card border transition-colors duration-300', colors.border)}>
            <div className="px-4 py-3 border-b border-white/[0.08] flex items-center justify-between">
              <p className="text-sm font-semibold text-white">Live Readings</p>
              {sensors?.last_reading_at && (
                <span className="text-[10px] text-gray-600">
                  Updated {formatRelative(sensors.last_reading_at)}
                </span>
              )}
            </div>
            <div className="grid grid-cols-2 gap-2 p-4">
              <SensorTile
                metric="temperature"
                value={sensors?.temperature ?? null}
                status={sensors?.temp_status ?? 'unknown'}
              />
              <SensorTile
                metric="humidity"
                value={sensors?.humidity ?? null}
                status={sensors?.humidity_status ?? 'unknown'}
              />
              <SensorTile
                metric="pm25"
                value={sensors?.pm25 ?? null}
                status={sensors?.pm25_status ?? 'unknown'}
              />
              <SensorTile
                metric="pm10"
                value={sensors?.pm10 ?? null}
                status={sensors?.pm10_status ?? 'unknown'}
              />
              {sensors?.pressure != null && (
                <SensorTile
                  metric="pressure"
                  value={sensors.pressure}
                  status="good"
                />
              )}
              {sensors?.gas_resistance != null && (
                <SensorTile
                  metric="gas_resistance"
                  value={Math.round(sensors.gas_resistance / 1000)}
                  status="good"
                />
              )}
              {sensors?.iaq != null && (
                <SensorTile
                  metric="iaq"
                  value={sensors.iaq}
                  status={sensors.iaq_status}
                  className="col-span-2"
                />
              )}
            </div>
          </div>

          {/* Sensor history chart */}
          <div className="card p-5">
            <div className="flex items-center gap-2 mb-4">
              <TrendingUp className="h-4 w-4 text-electric-blue/70" />
              <h2 className="text-sm font-semibold text-white">Sensor History</h2>
            </div>
            <SensorHistoryChart pitId={pit.id} />
          </div>

          {/* Per-pit alert thresholds — owner/admin only */}
          {isOwnerOrAdmin && (
            <PitAlertConfigPanel
              pitId={pit.id}
              alertCfg={alertCfg}
              alertOpen={alertOpen}
              onToggle={() => {
                if (!alertOpen && !alertCfg) {
                  pitsApi.getAlertConfig(pit.id).then(setAlertCfg).catch(() => { })
                }
                setAlertOpen(!alertOpen)
              }}
              onSaved={(cfg) => setAlertCfg(cfg)}
            />
          )}
        </div>

        {/* RIGHT: Video feed + sensor data overlaid ────────────────── */}
        {canViewVideo && (
          <div className="lg:col-span-2 space-y-3">
            {/* ── Video container ── */}
            <div className="relative w-full aspect-video rounded-2xl overflow-hidden border border-white/10 shadow-2xl shadow-black/60 bg-black">
              {/* Stream fills the container */}
              <StreamTokenLoader
                pitId={pit.id}
                cameraIsOnline={pit.camera_is_online}
                cameraLastSeen={pit.camera_last_seen}
                className="absolute inset-0 w-full h-full"
              />

              {/* Top gradient — improves overlay card readability */}
              <div className="absolute inset-x-0 top-0 h-32 bg-gradient-to-b from-black/70 to-transparent pointer-events-none z-[5]" />
              {/* Bottom gradient */}
              <div className="absolute inset-x-0 bottom-0 h-28 bg-gradient-to-t from-black/80 to-transparent pointer-events-none z-[5]" />

              {/* ── Sensor overlay — top right ── */}
              <div className="absolute top-4 right-4 z-20 flex flex-col gap-2">
                {/* Temperature */}
                <div className={overlayCard} style={overlayCardStyle}>
                  <div className="p-1.5 rounded-lg bg-electric-blue/10 shrink-0">
                    <Thermometer className="h-4 w-4 text-electric-blue" />
                  </div>
                  <div>
                    <p className="text-[9px] font-medium text-gray-400 uppercase tracking-[0.15em] leading-none mb-1">
                      Temperature
                    </p>
                    <p className="text-sm font-mono font-bold text-white leading-none">
                      {sensors?.temperature != null
                        ? `${sensors.temperature.toFixed(1)}°C`
                        : '—'}
                    </p>
                  </div>
                </div>

                {/* Humidity */}
                <div className={overlayCard} style={overlayCardStyle}>
                  <div className="p-1.5 rounded-lg bg-blue-500/10 shrink-0">
                    <Droplets className="h-4 w-4 text-blue-400" />
                  </div>
                  <div>
                    <p className="text-[9px] font-medium text-gray-400 uppercase tracking-[0.15em] leading-none mb-1">
                      Humidity
                    </p>
                    <p className="text-sm font-mono font-bold text-white leading-none">
                      {sensors?.humidity != null
                        ? `${sensors.humidity.toFixed(0)}%`
                        : '—'}
                    </p>
                  </div>
                </div>

                {/* PM 2.5 — only when sensor is reporting */}
                {sensors?.pm25 != null && (
                  <div className={overlayCard} style={overlayCardStyle}>
                    <div className="p-1.5 rounded-lg bg-emerald-500/10 shrink-0">
                      <Wind className="h-4 w-4 text-emerald-400" />
                    </div>
                    <div>
                      <p className="text-[9px] font-medium text-gray-400 uppercase tracking-[0.15em] leading-none mb-1">
                        Air Quality
                      </p>
                      <p className="text-sm font-mono font-bold text-white leading-none">
                        {sensors.pm25.toFixed(1)}{' '}
                        <span className="text-[9px] text-gray-500 font-normal">
                          μg/m³
                        </span>
                      </p>
                    </div>
                  </div>
                )}

                {/* IAQ — only when sensor is reporting */}
                {sensors?.iaq != null && (
                  <div className={overlayCard} style={overlayCardStyle}>
                    <div className="p-1.5 rounded-lg bg-purple-500/10 shrink-0">
                      <Gauge className="h-4 w-4 text-purple-400" />
                    </div>
                    <div>
                      <p className="text-[9px] font-medium text-gray-400 uppercase tracking-[0.15em] leading-none mb-1">
                        Air Quality Index
                      </p>
                      <p className="text-sm font-mono font-bold text-white leading-none">
                        {sensors.iaq.toFixed(0)}{' '}
                        <span className="text-[9px] text-gray-500 font-normal">
                          IAQ
                        </span>
                      </p>
                    </div>
                  </div>
                )}

                {/* Pressure — only when BME688 is reporting */}
                {sensors?.pressure != null && (
                  <div className={overlayCard} style={overlayCardStyle}>
                    <div className="p-1.5 rounded-lg bg-amber-500/10 shrink-0">
                      <BarChart3 className="h-4 w-4 text-amber-400" />
                    </div>
                    <div>
                      <p className="text-[9px] font-medium text-gray-400 uppercase tracking-[0.15em] leading-none mb-1">
                        Pressure
                      </p>
                      <p className="text-sm font-mono font-bold text-white leading-none">
                        {sensors.pressure.toFixed(1)}{' '}
                        <span className="text-[9px] text-gray-500 font-normal">
                          hPa
                        </span>
                      </p>
                    </div>
                  </div>
                )}
              </div>

              {/* ── Camera label — bottom left ── */}
              <CameraTimestamp pitNumber={pit.pit_number} pitName={pit.name} />
            </div>

            {/* ── Camera status strip ── */}
            <div className="flex items-center justify-between px-1">
              <div className="flex items-center gap-2">
                {pit.camera_is_online ? (
                  <span className="flex items-center gap-1.5 text-[11px] text-emerald-400">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-400 animate-pulse" />
                    Camera Online
                  </span>
                ) : (
                  <span className="flex items-center gap-1.5 text-[11px] text-gray-600">
                    <span className="h-1.5 w-1.5 rounded-full bg-gray-600" />
                    Camera Offline
                  </span>
                )}
                {pit.camera_model && (
                  <span className="text-[11px] text-gray-600 font-mono">
                    · {pit.camera_model}
                  </span>
                )}
              </div>
              {pit.camera_last_seen && !pit.camera_is_online && (
                <span className="text-[11px] text-gray-600">
                  Last seen {formatRelative(pit.camera_last_seen)}
                </span>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
