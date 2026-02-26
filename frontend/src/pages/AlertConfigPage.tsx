import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { useAppSelector } from '@/hooks/useAppDispatch'
import { alertsApi } from '@/api/alerts'
import type { AlertConfigUpdate } from '@/types/alert'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { PageSpinner } from '@/components/ui/Spinner'
import { ArrowLeft } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import toast from 'react-hot-toast'

export default function AlertConfigPage() {
  const navigate = useNavigate()
  const workshopId = useAppSelector((s) => s.auth.user?.workshop_id)
  const [loading, setLoading] = useState(true)

  const { register, handleSubmit, reset } = useForm<AlertConfigUpdate>()

  useEffect(() => {
    if (!workshopId) return
    alertsApi
      .getConfig(workshopId)
      .then((cfg) => {
        reset({
          temp_min: cfg.temp_min,
          temp_max: cfg.temp_max,
          humidity_max: cfg.humidity_max,
          pm25_warning: cfg.pm25_warning,
          pm25_critical: cfg.pm25_critical,
          pm10_warning: cfg.pm10_warning,
          pm10_critical: cfg.pm10_critical,
          iaq_warning: cfg.iaq_warning,
          iaq_critical: cfg.iaq_critical,
          device_offline_threshold_seconds: cfg.device_offline_threshold_seconds,
        })
      })
      .catch(() => toast.error('Failed to load config'))
      .finally(() => setLoading(false))
  }, [workshopId, reset])

  const onSubmit = async (data: AlertConfigUpdate) => {
    if (!workshopId) return
    try {
      await alertsApi.updateConfig(workshopId, data)
      toast.success('Alert thresholds saved!')
    } catch {
      toast.error('Failed to save config')
    }
  }

  if (loading) return <PageSpinner />

  return (
    <div className="p-6 max-w-2xl mx-auto">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-sm text-gray-400 hover:text-white mb-5"
      >
        <ArrowLeft className="h-4 w-4" />
        Back to Alerts
      </button>

      <h1 className="text-xl font-bold text-white mb-6">Alert Thresholds</h1>

      <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
        {/* Temperature */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-200 mb-4">Temperature (°C)</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Min" type="number" step="0.1" {...register('temp_min', { valueAsNumber: true })} />
            <Input label="Max" type="number" step="0.1" {...register('temp_max', { valueAsNumber: true })} />
          </div>
        </div>

        {/* Humidity */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-200 mb-4">Humidity (%)</h2>
          <Input label="Max" type="number" step="0.1" {...register('humidity_max', { valueAsNumber: true })} />
        </div>

        {/* PM2.5 */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-200 mb-4">PM2.5 (μg/m³)</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Warning" type="number" step="0.1" {...register('pm25_warning', { valueAsNumber: true })} />
            <Input label="Critical" type="number" step="0.1" {...register('pm25_critical', { valueAsNumber: true })} />
          </div>
        </div>

        {/* PM10 */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-200 mb-4">PM10 (μg/m³)</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Warning" type="number" step="0.1" {...register('pm10_warning', { valueAsNumber: true })} />
            <Input label="Critical" type="number" step="0.1" {...register('pm10_critical', { valueAsNumber: true })} />
          </div>
        </div>

        {/* IAQ */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-200 mb-4">Air Quality Index</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="Warning" type="number" step="1" {...register('iaq_warning', { valueAsNumber: true })} />
            <Input label="Critical" type="number" step="1" {...register('iaq_critical', { valueAsNumber: true })} />
          </div>
        </div>

        {/* Device offline */}
        <div className="card p-5">
          <h2 className="font-semibold text-gray-200 mb-4">Device Offline Threshold (seconds)</h2>
          <Input type="number" step="1" {...register('device_offline_threshold_seconds', { valueAsNumber: true })} />
        </div>

        <div className="flex justify-end">
          <Button type="submit">Save Thresholds</Button>
        </div>
      </form>
    </div>
  )
}
