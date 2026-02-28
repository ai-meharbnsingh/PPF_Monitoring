import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Car, Search, Video, Thermometer, Droplets, Wind } from 'lucide-react'
import toast from 'react-hot-toast'

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
}

interface SensorData {
  temperature: number | null
  humidity: number | null
  pm25: number | null
  pm10: number | null
  is_device_online: boolean
  last_reading_at: string | null
}

export default function TrackByCodePage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const initialCode = searchParams.get('code') || ''
  const [code, setCode] = useState(initialCode)
  const [loading, setLoading] = useState(false)
  const [jobData, setJobData] = useState<TrackingData | null>(null)
  const [sensorData, setSensorData] = useState<SensorData | null>(null)

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
      // Fetch job by tracking code
      const jobRes = await fetch(`/api/v1/track/code/${lookupCode}`)
      if (!jobRes.ok) {
        if (jobRes.status === 404) {
          toast.error('Tracking code not found')
        } else {
          toast.error('Error fetching job data')
        }
        setLoading(false)
        return
      }
      
      const job = await jobRes.json()
      setJobData(job)

      // Fetch sensor data for the pit
      try {
        const sensorRes = await fetch(`/api/v1/pits/${job.pit_id}/sensors/latest`)
        if (sensorRes.ok) {
          const sensor = await sensorRes.json()
          setSensorData(sensor)
        }
      } catch (e) {
        // Sensor data is optional
        console.log('No sensor data available')
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
      case 'completed': return 'text-emerald-400'
      case 'in_progress': return 'text-blue-400'
      case 'quality_check': return 'text-amber-400'
      case 'waiting': return 'text-gray-400'
      default: return 'text-gray-400'
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

  return (
    <div className="min-h-screen bg-gradient-to-b from-black via-[#0a0a0a] to-[#111]">
      {/* Header */}
      <div className="border-b border-white/10 bg-black/50 backdrop-blur-sm">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-3">
            <Car className="h-8 w-8 text-electric-blue" />
            <h1 className="text-2xl font-bold text-white">PPF Workshop</h1>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {!jobData ? (
          /* Code Entry Form */
          <div className="max-w-md mx-auto">
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
                  placeholder="e.g., 847291"
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

            <div className="mt-8 text-center">
              <p className="text-sm text-gray-500">
                Don't have a code? Contact your workshop to get one.
              </p>
            </div>
          </div>
        ) : (
          /* Job Details View */
          <div className="space-y-6">
            {/* Back Button */}
            <Button
              variant="secondary"
              onClick={() => {
                setJobData(null)
                setSensorData(null)
                setCode('')
              }}
            >
              ← Track Another Car
            </Button>

            {/* Car Info Card */}
            <div className="card p-6">
              <div className="flex items-start justify-between">
                <div>
                  <div className="flex items-center gap-3 mb-2">
                    <Car className="h-6 w-6 text-electric-blue" />
                    <h2 className="text-2xl font-bold text-white">
                      {jobData.car_model || 'Your Vehicle'}
                    </h2>
                  </div>
                  {jobData.car_plate && (
                    <p className="text-lg text-gray-400 font-mono">{jobData.car_plate}</p>
                  )}
                  {(jobData.car_color || jobData.car_year) && (
                    <p className="text-sm text-gray-500 mt-1">
                      {jobData.car_color} {jobData.car_year}
                    </p>
                  )}
                </div>
                <div className="text-right">
                  <p className="text-sm text-gray-500">Tracking Code</p>
                  <p className="text-2xl font-mono font-bold text-electric-blue">
                    {jobData.tracking_code}
                  </p>
                </div>
              </div>

              <div className="mt-4 pt-4 border-t border-white/10">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-gray-500">Workshop</p>
                    <p className="text-white font-medium">{jobData.workshop_name}</p>
                  </div>
                  <div>
                    <p className="text-sm text-gray-500">Bay</p>
                    <p className="text-white font-medium">{jobData.pit_display_name}</p>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-500">Status</p>
                    <p className={`font-medium ${getStatusColor(jobData.status)}`}>
                      {getStatusLabel(jobData.status)}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            {/* Progress */}
            <div className="card p-6">
              <h3 className="text-lg font-semibold text-white mb-4">Work Progress</h3>
              <div className="relative pt-1">
                <div className="flex mb-2 items-center justify-between">
                  <div>
                    <span className="text-xs font-semibold inline-block py-1 px-2 uppercase rounded-full text-electric-blue bg-electric-blue/10">
                      {jobData.progress_percent}%
                    </span>
                  </div>
                  {jobData.remaining_minutes !== null && jobData.remaining_minutes > 0 && (
                    <div className="text-right">
                      <span className="text-xs font-semibold inline-block text-gray-400">
                        ~{Math.ceil(jobData.remaining_minutes)} mins remaining
                      </span>
                    </div>
                  )}
                </div>
                <div className="overflow-hidden h-2 mb-4 text-xs flex rounded bg-white/10">
                  <div
                    style={{ width: `${jobData.progress_percent}%` }}
                    className="shadow-none flex flex-col text-center whitespace-nowrap text-white justify-center bg-electric-blue"
                  />
                </div>
              </div>
            </div>

            {/* Live Video */}
            <div className="card p-6">
              <div className="flex items-center gap-2 mb-4">
                <Video className="h-5 w-5 text-red-500" />
                <h3 className="text-lg font-semibold text-white">Live Camera</h3>
                <span className="flex items-center gap-1 text-xs text-red-400">
                  <span className="h-2 w-2 rounded-full bg-red-500 animate-pulse" />
                  LIVE
                </span>
              </div>
              <div className="aspect-video bg-black rounded-lg overflow-hidden border border-white/10 flex items-center justify-center">
                <p className="text-gray-500">Video stream will appear here</p>
              </div>
            </div>

            {/* Sensor Data */}
            {sensorData && (
              <div className="card p-6">
                <h3 className="text-lg font-semibold text-white mb-4">Environment</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="bg-white/5 rounded-lg p-4 text-center">
                    <Thermometer className="h-6 w-6 text-orange-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      {sensorData.temperature?.toFixed(1) || '--'}°C
                    </p>
                    <p className="text-xs text-gray-500">Temperature</p>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4 text-center">
                    <Droplets className="h-6 w-6 text-blue-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      {sensorData.humidity?.toFixed(0) || '--'}%
                    </p>
                    <p className="text-xs text-gray-500">Humidity</p>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4 text-center">
                    <Wind className="h-6 w-6 text-purple-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      {sensorData.pm25?.toFixed(0) || '--'}
                    </p>
                    <p className="text-xs text-gray-500">PM2.5</p>
                  </div>
                  <div className="bg-white/5 rounded-lg p-4 text-center">
                    <Wind className="h-6 w-6 text-emerald-400 mx-auto mb-2" />
                    <p className="text-2xl font-bold text-white">
                      {sensorData.pm10?.toFixed(0) || '--'}
                    </p>
                    <p className="text-xs text-gray-500">PM10</p>
                  </div>
                </div>
                <div className="mt-4 flex items-center justify-between text-sm">
                  <span className={sensorData.is_device_online ? 'text-emerald-400' : 'text-red-400'}>
                    {sensorData.is_device_online ? '● Sensors Online' : '● Sensors Offline'}
                  </span>
                  {sensorData.last_reading_at && (
                    <span className="text-gray-500">
                      Updated: {new Date(sensorData.last_reading_at).toLocaleTimeString()}
                    </span>
                  )}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  )
}
