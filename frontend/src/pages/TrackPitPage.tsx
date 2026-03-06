import { useState } from 'react'
import { Search, Video, Thermometer, Wind, Activity } from 'lucide-react'
import { VideoPlayer } from '@/components/video/VideoPlayer'

interface PitData {
  pit_id: number
  pit_name: string
  pit_number: number
  tracking_code: string
  camera_is_online: boolean
  camera_model: string
  stream: {
    token: string
    expires_at: string
    hls_url: string
    webrtc_url: string
  }
  latest_sensor: {
    temperature: number
    humidity: number
    pm25: number
    pm10: number
    iaq: number
    timestamp: string
  } | null
}

export default function TrackPitPage() {
  const [code, setCode] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [pitData, setPitData] = useState<PitData | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (code.length !== 6 || !/\d{6}/.test(code)) {
      setError('Please enter a valid 6-digit code')
      return
    }

    setLoading(true)
    setError('')
    
    try {
      const response = await fetch(`http://localhost:8000/api/v1/track/pit/${code}`)
      if (!response.ok) {
        if (response.status === 404) {
          throw new Error('Tracking code not found')
        }
        throw new Error('Failed to fetch pit data')
      }
      
      const data = await response.json()
      setPitData(data)
    } catch (err: any) {
      setError(err.message || 'Failed to track pit')
      setPitData(null)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-950 flex flex-col">
      {/* Header */}
      <header className="bg-gray-900 border-b border-white/10 px-6 py-4">
        <div className="max-w-6xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 bg-electric-blue rounded-lg flex items-center justify-center">
              <Video className="h-5 w-5 text-white" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-white">RG Studio</h1>
              <p className="text-xs text-gray-500">Track Your Vehicle</p>
            </div>
          </div>
        </div>
      </header>

      <main className="flex-1 flex flex-col items-center justify-center p-6">
        {!pitData ? (
          <div className="w-full max-w-md">
            <div className="text-center mb-8">
              <div className="inline-flex items-center justify-center h-16 w-16 bg-electric-blue/10 rounded-full mb-4">
                <Search className="h-8 w-8 text-electric-blue" />
              </div>
              <h2 className="text-2xl font-bold text-white mb-2">
                Track Your Vehicle
              </h2>
              <p className="text-gray-400">
                Enter your 6-digit tracking code to view your bay
              </p>
            </div>

            <form onSubmit={handleSubmit} className="space-y-4">
              <div>
                <input
                  type="text"
                  inputMode="numeric"
                  pattern="\d{6}"
                  maxLength={6}
                  placeholder="Enter 6-digit code (e.g., 437367)"
                  value={code}
                  onChange={(e) => setCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  className="w-full bg-black/50 border border-white/10 rounded-xl px-4 py-4 text-center text-2xl tracking-widest text-white placeholder:text-gray-600 focus:border-electric-blue focus:ring-2 focus:ring-electric-blue/20 outline-none transition-all"
                  disabled={loading}
                />
              </div>

              {error && (
                <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/30 text-red-400 text-sm text-center">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading || code.length !== 6}
                className="w-full bg-electric-blue hover:bg-electric-blue/90 disabled:opacity-50 disabled:cursor-not-allowed text-white font-semibold py-4 rounded-xl transition-all flex items-center justify-center gap-2"
              >
                {loading ? (
                  <>
                    <div className="h-5 w-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="h-5 w-5" />
                    Track My Vehicle
                  </>
                )}
              </button>
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
          <div className="w-full max-w-5xl animate-in fade-in duration-500">
            {/* Back button */}
            <button
              onClick={() => {
                setPitData(null)
                setCode('')
                setError('')
              }}
              className="mb-4 text-sm text-gray-400 hover:text-white transition-colors flex items-center gap-1"
            >
              ← Back to search
            </button>

            {/* Pit Header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white">{pitData.pit_name}</h2>
                <p className="text-gray-500">Bay #{pitData.pit_number}</p>
              </div>
              <div className="flex items-center gap-2 px-3 py-1.5 bg-emerald-500/10 border border-emerald-500/30 rounded-full">
                <div className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse" />
                <span className="text-xs text-emerald-400 font-medium">Live</span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              {/* Video Stream */}
              <div className="lg:col-span-2 space-y-4">
                <div className="aspect-video rounded-2xl overflow-hidden bg-black border border-white/10">
                  <VideoPlayer
                    webrtcUrl={pitData.stream.webrtc_url}
                    hlsUrl={pitData.stream.hls_url}
                    isOnline={pitData.camera_is_online}
                    cameraLastSeen={new Date().toISOString()}
                    className="w-full h-full"
                  />
                </div>
                
                <div className="flex items-center justify-between text-xs text-gray-500 px-1">
                  <span>Code: {pitData.tracking_code}</span>
                  <span>{pitData.camera_model}</span>
                </div>
              </div>

              {/* Sensor Data */}
              <div className="space-y-4">
                <h3 className="text-sm font-semibold text-gray-400 uppercase tracking-wider">
                  Live Readings
                </h3>

                {pitData.latest_sensor ? (
                  <div className="grid grid-cols-2 gap-3">
                    {/* Temperature */}
                    <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                      <div className="flex items-center gap-2 text-electric-blue mb-2">
                        <Thermometer className="h-4 w-4" />
                        <span className="text-xs font-medium">Temperature</span>
                      </div>
                      <p className="text-2xl font-bold text-white">
                        {pitData.latest_sensor.temperature?.toFixed(1) ?? '--'}°C
                      </p>
                    </div>

                    {/* Humidity */}
                    <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                      <div className="flex items-center gap-2 text-blue-400 mb-2">
                        <Activity className="h-4 w-4" />
                        <span className="text-xs font-medium">Humidity</span>
                      </div>
                      <p className="text-2xl font-bold text-white">
                        {pitData.latest_sensor.humidity?.toFixed(0) ?? '--'}%
                      </p>
                    </div>

                    {/* PM2.5 */}
                    <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                      <div className="flex items-center gap-2 text-orange-400 mb-2">
                        <Wind className="h-4 w-4" />
                        <span className="text-xs font-medium">PM2.5</span>
                      </div>
                      <p className="text-2xl font-bold text-white">
                        {pitData.latest_sensor.pm25?.toFixed(0) ?? '--'}
                      </p>
                      <p className="text-xs text-gray-500">μg/m³</p>
                    </div>

                    {/* IAQ */}
                    <div className="bg-white/5 border border-white/10 rounded-xl p-4">
                      <div className="flex items-center gap-2 text-purple-400 mb-2">
                        <Activity className="h-4 w-4" />
                        <span className="text-xs font-medium">Air Quality</span>
                      </div>
                      <p className="text-2xl font-bold text-white">
                        {pitData.latest_sensor.iaq?.toFixed(0) ?? '--'}
                      </p>
                      <p className="text-xs text-gray-500">IAQ</p>
                    </div>
                  </div>
                ) : (
                  <div className="bg-white/5 border border-white/10 rounded-xl p-8 text-center">
                    <p className="text-gray-500">No sensor data available</p>
                  </div>
                )}

                <p className="text-xs text-gray-600 text-center">
                  Last updated: {pitData.latest_sensor?.timestamp 
                    ? new Date(pitData.latest_sensor.timestamp).toLocaleTimeString() 
                    : 'Never'}
                </p>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  )
}
