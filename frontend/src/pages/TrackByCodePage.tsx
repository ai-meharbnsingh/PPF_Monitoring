import { useState, useEffect, useRef } from 'react'
import { useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { VideoPlayer } from '@/components/video/VideoPlayer'
import { Car, Search, Video, Thermometer, Droplets, Wind, Activity, Clock, Wrench } from 'lucide-react'
import toast from 'react-hot-toast'
import { clsx } from 'clsx'

interface TrackingData {
  job_id: number
  tracking_code: string
  work_type: string
  status: string
  car_model: string | null
  car_plate: string | null
  car_color: string | null
  car_year: number | null
  progress_percent: number
  remaining_minutes: number | null
  pit_display_name: string
  workshop_name: string
  pit_id: number
  camera_is_online: boolean
}

interface SensorData {
  temperature: number | null
  humidity: number | null
  pm25: number | null
  pm10: number | null
  iaq: number | null
  pressure: number | null
  is_device_online: boolean
  last_reading_at: string | null
}

// Work progress config for each pit
const PIT_WORK_CONFIG: Record<number, { type: string; progress: number; status: string; eta: string }> = {
  3: { type: 'PPF Installation - Front Bumper', progress: 75, status: 'in_progress', eta: '45 min' },
  4: { type: 'Ceramic Coating - Full Body', progress: 30, status: 'in_progress', eta: '2 hours' },
  5: { type: 'Paint Protection - Side Doors', progress: 90, status: 'quality_check', eta: '15 min' },
}

export default function TrackByCodePage() {
  const [searchParams] = useSearchParams()
  const initialCode = searchParams.get('code') || ''
  const [code, setCode] = useState(initialCode)
  const [loading, setLoading] = useState(false)
  const [jobData, setJobData] = useState<TrackingData | null>(null)
  const [sensorData, setSensorData] = useState<SensorData | null>(null)
  const [streamUrls, setStreamUrls] = useState<{ webrtcUrl: string; hlsUrl: string } | null>(null)

  // Auto-submit if code is provided in URL
  useEffect(() => {
    if (initialCode.length === 6 && /^[0-9]+$/.test(initialCode)) {
      handleLookup(initialCode)
    }
  }, [initialCode])

  const handleLookup = async (lookupCode: string) => {
    if (!lookupCode || lookupCode.length !== 6 || !/^[0-9]+$/.test(lookupCode)) {
      toast.error('Please enter a valid 6-digit code')
      return
    }

    setLoading(true)
    try {
      // First, try to fetch job by tracking code
      const jobRes = await fetch(`/api/v1/track/code/${lookupCode}`)
      
      if (jobRes.ok) {
        // Job found - use job tracking
        const job: TrackingData = await jobRes.json()
        setJobData(job)

        // Fetch sensor data for job
        try {
          const sensorRes = await fetch(`/api/v1/track/code/${lookupCode}/sensors`)
          if (sensorRes.ok) {
            const sensor = await sensorRes.json()
            setSensorData(sensor)
          }
        } catch {
          // Sensor data is optional
        }

        // Fetch stream token for job
        if (job.camera_is_online) {
          try {
            const streamRes = await fetch(`/api/v1/track/code/${lookupCode}/stream-token`)
            if (streamRes.ok) {
              const stream = await streamRes.json()
              let hlsUrl = stream.hls_url ?? ''
              const webrtcUrl = stream.webrtc_url ?? ''
              
              if (!hlsUrl && webrtcUrl) {
                hlsUrl = webrtcUrl.replace('/whep', '/index.m3u8')
              }
              
              setStreamUrls({ webrtcUrl, hlsUrl })
            }
          } catch (err) {
            console.error('Stream token fetch error:', err)
          }
        }
      } else if (jobRes.status === 404) {
        // Job not found - try pit tracking code
        const pitRes = await fetch(`/api/v1/track/pit/${lookupCode}`)
        
        if (pitRes.ok) {
          const pitData = await pitRes.json()
          
          // Get work config for this pit
          const workConfig = PIT_WORK_CONFIG[pitData.pit_id] || { 
            type: 'General Service', 
            progress: 50, 
            status: 'in_progress',
            eta: '1 hour'
          }
          
          // Create job-like data from pit data
          const mockJobData: TrackingData = {
            job_id: pitData.pit_id,
            tracking_code: lookupCode,
            work_type: workConfig.type,
            status: workConfig.status,
            car_model: 'Customer Vehicle',
            car_plate: null,
            car_color: null,
            car_year: null,
            progress_percent: workConfig.progress,
            remaining_minutes: workConfig.eta.includes('min') ? parseInt(workConfig.eta) : null,
            pit_display_name: pitData.pit_name,
            workshop_name: 'RG Studio',
            pit_id: pitData.pit_id,
            camera_is_online: pitData.camera_is_online,
          }
          setJobData(mockJobData)
          
          // Set sensor data from pit
          if (pitData.latest_sensor) {
            setSensorData({
              temperature: pitData.latest_sensor.temperature,
              humidity: pitData.latest_sensor.humidity,
              pm25: pitData.latest_sensor.pm25,
              pm10: pitData.latest_sensor.pm10,
              iaq: pitData.latest_sensor.iaq,
              pressure: pitData.latest_sensor.pressure,
              is_device_online: true,
              last_reading_at: pitData.latest_sensor.timestamp,
            })
          }
          
          // Set stream URLs from pit
          if (pitData.stream) {
            setStreamUrls({
              webrtcUrl: pitData.stream.webrtc_url,
              hlsUrl: pitData.stream.hls_url,
            })
          }
        } else {
          toast.error('Tracking code not found')
        }
      } else {
        toast.error('Error fetching data')
      }

    } catch (error) {
      toast.error('Network error')
    } finally {
      setLoading(false)
    }
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    handleLookup(code)
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'text-emerald-400 bg-emerald-500/10 border-emerald-500/30'
      case 'in_progress': return 'text-blue-400 bg-blue-500/10 border-blue-500/30'
      case 'quality_check': return 'text-amber-400 bg-amber-500/10 border-amber-500/30'
      case 'waiting': return 'text-gray-400 bg-gray-500/10 border-gray-500/30'
      default: return 'text-gray-400 bg-gray-500/10 border-gray-500/30'
    }
  }

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'waiting': return 'Waiting'
      case 'in_progress': return 'In Progress'
      case 'quality_check': return 'Quality Check'
      case 'completed': return 'Completed'
      default: return status
    }
  }

  // Sensor overlay card style
  const overlayCard = 'flex items-center gap-2 px-3 py-2 rounded-lg min-w-[130px]'
  const overlayCardStyle = {
    background: 'rgba(8,8,8,0.85)',
    backdropFilter: 'blur(12px)',
    WebkitBackdropFilter: 'blur(12px)',
    border: '1px solid rgba(255,255,255,0.08)',
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-[#0a0a0a] to-[#111]">
      {/* Header */}
      <div className="border-b border-white/10 bg-black/50 backdrop-blur-sm">
        <div className="max-w-6xl mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Car className="h-8 w-8 text-electric-blue" />
              <h1 className="text-2xl font-bold text-white">RG Studio</h1>
            </div>
            {jobData && (
              <Button
                variant="secondary"
                size="sm"
                onClick={() => {
                  setJobData(null)
                  setSensorData(null)
                  setStreamUrls(null)
                  setCode('')
                }}
              >
                ← Back
              </Button>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-6">
        {!jobData ? (
          /* Code Entry Form */
          <div className="max-w-md mx-auto pt-12">
            <div className="text-center mb-8">
              <div className="w-20 h-20 bg-electric-blue/10 rounded-full flex items-center justify-center mx-auto mb-4">
                <Search className="h-10 w-10 text-electric-blue" />
              </div>
              <h2 className="text-3xl font-bold text-white mb-2">Track Your Car</h2>
              <p className="text-gray-400">Enter the 6-digit code provided by your workshop</p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  6-Digit Tracking Code
                </label>
                <Input
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/[^0-9]/g, '').slice(0, 6))}
                  placeholder="e.g., 437367"
                  maxLength={6}
                  className="text-center text-2xl tracking-widest font-mono"
                  autoFocus
                />
              </div>
              <Button
                type="submit"
                className="w-full py-4 text-lg"
                isLoading={loading}
                disabled={code.length !== 6}
              >
                Track My Car
              </Button>
            </form>

            <div className="mt-8 p-4 bg-white/5 rounded-xl border border-white/10">
              <p className="text-xs text-gray-500 text-center">
                <strong className="text-gray-400">Demo Codes:</strong>
                <br />
                Pit One: 437367 | Pit Two: 167325 | Pit Three: 877606
              </p>
            </div>
          </div>
        ) : (
          /* Job Details View with Sensor Overlay */
          <div className="space-y-6">
            {/* Work Info Card */}
            <div className="card p-5">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-start gap-4">
                  <div className={clsx(
                    "h-12 w-12 rounded-xl flex items-center justify-center shrink-0",
                    getStatusColor(jobData.status).split(' ')[1]
                  )}>
                    <Wrench className={clsx("h-6 w-6", getStatusColor(jobData.status).split(' ')[0])} />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white">{jobData.work_type}</h2>
                    <p className="text-gray-500">{jobData.pit_display_name} • {jobData.workshop_name}</p>
                  </div>
                </div>
                <div className={clsx(
                  "flex items-center gap-2 px-4 py-2 rounded-full border",
                  getStatusColor(jobData.status)
                )}>
                  <Clock className="h-4 w-4" />
                  <span className="font-medium">{getStatusLabel(jobData.status)}</span>
                </div>
              </div>
              
              {/* Progress Bar */}
              <div className="mt-4">
                <div className="flex items-center justify-between text-sm mb-2">
                  <span className="text-gray-400">Progress</span>
                  <span className="text-white font-medium">{jobData.progress_percent}%</span>
                </div>
                <div className="h-2 bg-gray-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-electric-blue to-blue-400 rounded-full transition-all"
                    style={{ width: `${jobData.progress_percent}%` }}
                  />
                </div>
              </div>
            </div>

            {/* Live Video with Sensor Overlay */}
            <div className="relative rounded-2xl overflow-hidden border border-white/10 shadow-2xl">
              {/* Header overlay */}
              <div className="absolute top-0 left-0 right-0 h-16 bg-gradient-to-b from-black/80 to-transparent z-10 pointer-events-none" />
              
              {/* LIVE badge */}
              <div className="absolute top-4 right-4 z-20 flex items-center gap-1.5 px-3 py-1.5 bg-red-500/20 border border-red-500/40 rounded-full">
                <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
                <span className="text-xs text-red-400 font-bold tracking-wider">LIVE</span>
              </div>

              {/* Video Player */}
              <div className="aspect-video bg-black">
                <VideoPlayer
                  webrtcUrl={streamUrls?.webrtcUrl ?? ''}
                  hlsUrl={streamUrls?.hlsUrl ?? ''}
                  pitName={jobData.pit_display_name}
                  isOnline={jobData.camera_is_online}
                  className="w-full h-full"
                />
              </div>

              {/* Bottom gradient */}
              <div className="absolute bottom-0 left-0 right-0 h-48 bg-gradient-to-t from-black/90 via-black/50 to-transparent pointer-events-none z-10" />

              {/* Sensor Overlays - Bottom Left */}
              {sensorData?.is_device_online && (
                <div className="absolute bottom-4 left-4 z-20 flex flex-col gap-2">
                  {/* Temperature */}
                  <div className={overlayCard} style={overlayCardStyle}>
                    <div className="p-1.5 rounded-md bg-electric-blue/20">
                      <Thermometer className="h-4 w-4 text-electric-blue" />
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-400 uppercase">Temp</p>
                      <p className="text-sm font-bold text-white">
                        {sensorData.temperature?.toFixed(1) ?? '--'}°C
                      </p>
                    </div>
                  </div>

                  {/* Humidity */}
                  <div className={overlayCard} style={overlayCardStyle}>
                    <div className="p-1.5 rounded-md bg-blue-500/20">
                      <Droplets className="h-4 w-4 text-blue-400" />
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-400 uppercase">Humidity</p>
                      <p className="text-sm font-bold text-white">
                        {sensorData.humidity?.toFixed(0) ?? '--'}%
                      </p>
                    </div>
                  </div>

                  {/* PM2.5 */}
                  <div className={overlayCard} style={overlayCardStyle}>
                    <div className="p-1.5 rounded-md bg-orange-500/20">
                      <Wind className="h-4 w-4 text-orange-400" />
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-400 uppercase">PM2.5</p>
                      <p className="text-sm font-bold text-white">
                        {sensorData.pm25?.toFixed(0) ?? '--'}
                        <span className="text-[9px] text-gray-500 ml-1">μg/m³</span>
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Air Quality - Bottom Right */}
              {sensorData?.is_device_online && sensorData.iaq && (
                <div className="absolute bottom-4 right-4 z-20">
                  <div className={overlayCard} style={overlayCardStyle}>
                    <div className="p-1.5 rounded-md bg-purple-500/20">
                      <Activity className="h-4 w-4 text-purple-400" />
                    </div>
                    <div>
                      <p className="text-[10px] text-gray-400 uppercase">Air Quality</p>
                      <p className="text-sm font-bold text-white">
                        {sensorData.iaq.toFixed(0)}
                        <span className="text-[9px] text-gray-500 ml-1">IAQ</span>
                      </p>
                    </div>
                  </div>
                </div>
              )}

              {/* Camera Label - Bottom Center */}
              <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-20 pointer-events-none">
                <p className="text-[10px] font-mono text-gray-500 uppercase tracking-wider">
                  {jobData.pit_display_name} • Live Feed
                </p>
              </div>
            </div>

            {/* Info Footer */}
            <div className="flex flex-wrap items-center justify-between gap-4 text-sm text-gray-500">
              <div className="flex items-center gap-2">
                <Video className="h-4 w-4" />
                <span>Code: {jobData.tracking_code}</span>
              </div>
              <div>
                Last updated: {sensorData?.last_reading_at 
                  ? new Date(sensorData.last_reading_at).toLocaleTimeString() 
                  : 'Never'}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
