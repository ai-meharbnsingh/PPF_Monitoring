import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { pitsApi } from '@/api/pits'
import { sensorsApi } from '@/api/sensors'
import type { PitSummary } from '@/types/pit'
import type { LatestSensorSummary } from '@/types/sensor'
import { SensorCard } from '@/components/sensors/SensorCard'
import { SensorHistoryChart } from '@/components/sensors/SensorHistoryChart'
import { StreamTokenLoader } from '@/components/video/StreamTokenLoader'
import { PageSpinner } from '@/components/ui/Spinner'
import { RoleGuard } from '@/components/auth/ProtectedRoute'
import { ArrowLeft, Video, TrendingUp } from 'lucide-react'

export default function PitDetailPage() {
  const { pitId } = useParams<{ pitId: string }>()
  const navigate = useNavigate()
  const [pit, setPit] = useState<PitSummary | null>(null)
  const [sensors, setSensors] = useState<LatestSensorSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [showVideo, setShowVideo] = useState(false)

  useEffect(() => {
    if (!pitId) return
    const id = Number(pitId)
    setLoading(true)
    Promise.all([
      pitsApi.getPit(id),
      sensorsApi.latestForPit(id),
    ])
      .then(([pitData, sensorData]) => {
        setPit(pitData)
        setSensors(sensorData)
      })
      .catch(() => {})
      .finally(() => setLoading(false))
  }, [pitId])

  if (loading) return <PageSpinner />
  if (!pit) return null

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <button
        onClick={() => navigate(-1)}
        className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-800 mb-5"
      >
        <ArrowLeft className="h-4 w-4" />
        Back
      </button>

      <h1 className="text-xl font-bold text-gray-900 mb-5">
        {pit.name} — Pit #{pit.pit_number}
      </h1>

      {/* Sensor card */}
      {sensors && (
        <div className="mb-6">
          <SensorCard pit={pit} sensors={sensors} />
        </div>
      )}

      {/* History chart */}
      <div className="card p-5 mb-6">
        <div className="flex items-center gap-2 mb-4">
          <TrendingUp className="h-4 w-4 text-gray-400" />
          <h2 className="font-semibold text-gray-800">Sensor History</h2>
        </div>
        <SensorHistoryChart pitId={pit.id} />
      </div>

      {/* Video stream (owner/staff only) */}
      <RoleGuard roles={['owner', 'super_admin', 'staff']}>
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <Video className="h-4 w-4 text-gray-400" />
              <h2 className="font-semibold text-gray-800">Live Camera</h2>
            </div>
            <button
              onClick={() => setShowVideo((v) => !v)}
              className="text-sm text-blue-600 hover:text-blue-800"
            >
              {showVideo ? 'Hide' : 'Show Stream'}
            </button>
          </div>
          {showVideo && (
            <StreamTokenLoader
              pitId={pit.id}
              pitName={pit.name}
              cameraIsOnline={pit.camera_is_online}
              cameraLastSeen={pit.camera_last_seen}
              className="w-full aspect-video"
            />
          )}
          {!showVideo && !pit.camera_is_online && (
            <p className="text-sm text-gray-400">Camera is offline</p>
          )}
        </div>
      </RoleGuard>
    </div>
  )
}
