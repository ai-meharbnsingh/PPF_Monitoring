import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { trackingApi } from '@/api/tracking'
import type { JobTrackingResponse } from '@/types/job'
import { JobStatusFlow } from '@/components/jobs/JobStatusFlow'
import { JobStatusBadge } from '@/components/jobs/JobStatusBadge'
import { Spinner } from '@/components/ui/Spinner'
import { clsx } from 'clsx'
import { Car, MapPin, Clock, CheckCircle, Thermometer, Droplets, Wind, Video, Maximize2, Minimize2 } from 'lucide-react'
import { formatDate, getRemainingMinutes, formatDurationMinutes } from '@/utils/formatters'

export default function TrackingPage() {
  const { token } = useParams<{ token: string }>()
  const [job, setJob] = useState<JobTrackingResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [notFound, setNotFound] = useState(false)
  const [remaining, setRemaining] = useState<number | null>(null)
  const [isFullScreen, setIsFullScreen] = useState(false)

  const toggleFullScreen = () => {
    setIsFullScreen(!isFullScreen)
  }

  const fetchJob = async () => {
    if (!token) return
    try {
      const data = await trackingApi.getJobByToken(token)
      setJob(data)
      setRemaining(getRemainingMinutes(data.estimated_end_time))
    } catch (err: unknown) {
      const status = (err as { response?: { status?: number } })?.response?.status
      if (status === 404) setNotFound(true)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void fetchJob()
    // Poll every 60 seconds
    const id = setInterval(() => void fetchJob(), 60_000)
    return () => clearInterval(id)
  }, [token])

  // Live countdown
  useEffect(() => {
    if (job?.status === 'completed' || job?.status === 'cancelled') return
    const id = setInterval(() => {
      setRemaining(getRemainingMinutes(job?.estimated_end_time ?? null))
    }, 60_000)
    return () => clearInterval(id)
  }, [job])

  if (loading) {
    return (
      <div className="min-h-screen bg-matte-black flex items-center justify-center">
        <Spinner size="lg" label="Loading live feed…" className="text-electric-blue" />
      </div>
    )
  }

  if (notFound || !job) {
    return (
      <div className="min-h-screen bg-matte-black flex flex-col items-center justify-center p-8 text-center">
        <div className="text-6xl mb-4 opacity-50">📡</div>
        <h1 className="text-2xl font-bold text-white mb-2">Signal Lost</h1>
        <p className="text-gray-400">
          This tracking link is invalid or has expired.
        </p>
      </div>
    )
  }

  const isComplete = job.status === 'completed'
  const isCancelled = job.status === 'cancelled'
  const cardClass = "bg-white/5 border border-white/10 backdrop-blur-xl rounded-2xl p-5"

  return (
    <div className="min-h-screen bg-matte-black text-white relative overflow-hidden flex flex-col">
      {/* Ambient light */}
      <div className="absolute inset-0 pointer-events-none" style={{ background: 'radial-gradient(circle at 50% 30%, rgba(0, 240, 255, 0.1) 0%, transparent 60%)' }} />
      {/* Grid overlay */}
      <div className="absolute inset-x-0 inset-y-0 h-screen pointer-events-none opacity-[0.03]" style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,1) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,1) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

      <div className="relative z-10 w-full flex-1 flex flex-col">
        {/* Header */}
        <header className="px-6 py-5 border-b border-white/5 bg-black/20 backdrop-blur-sm">
          <div className="max-w-lg mx-auto flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="h-8 w-8 rounded-lg flex items-center justify-center backdrop-blur-md" style={{ background: 'rgba(0,240,255,0.1)', border: '1px solid rgba(0,240,255,0.3)', boxShadow: '0 0 10px rgba(0,240,255,0.2)' }}>
                <span className="text-electric-blue font-bold tracking-wider text-xs">PPF</span>
              </div>
              <span className="font-semibold text-gray-200">
                {job.workshop_name ?? 'Auto Studio'}
              </span>
            </div>
            <JobStatusBadge status={job.status} />
          </div>
        </header>

        <div className="max-w-lg mx-auto w-full px-4 py-6 space-y-4">
          {/* Completed banner */}
          {isComplete && (
            <div className="flex items-center gap-3 p-4 bg-emerald-500/10 border border-emerald-500/30 rounded-2xl">
              <CheckCircle className="h-6 w-6 text-emerald-400 shrink-0" />
              <div>
                <p className="font-semibold text-emerald-400">Your vehicle is ready!</p>
                <p className="text-sm text-emerald-500/80">
                  Work completed on {formatDate(job.actual_end_time)}
                </p>
              </div>
            </div>
          )}

          {/* Cancelled banner */}
          {isCancelled && (
            <div className="p-4 bg-red-500/10 border border-red-500/30 rounded-2xl">
              <p className="font-semibold text-red-400">Job Cancelled</p>
            </div>
          )}

          {/* Live Feed Placeholder */}
          {!isCancelled && (
            <div className={clsx("transition-all duration-300", isFullScreen ? "fixed inset-0 z-50 bg-matte-black p-4 flex flex-col" : "bg-white/5 border border-white/10 backdrop-blur-xl rounded-2xl p-1 relative group")}>
              <div className="absolute top-4 left-4 z-10 flex items-center gap-2 bg-black/50 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10">
                <div className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                <span className="text-[10px] font-semibold tracking-wider text-white uppercase">Live Bay Feed</span>
              </div>

              <div className="absolute top-4 right-4 z-10 flex items-center gap-2">
                <div className="bg-black/50 backdrop-blur-md px-3 py-1.5 rounded-full border border-white/10 hidden sm:block">
                  <span className="text-[10px] font-mono text-gray-300">CAM-01</span>
                </div>
                <button onClick={toggleFullScreen} className="bg-black/50 hover:bg-black/70 transition-colors backdrop-blur-md p-1.5 rounded-full border border-white/10 text-white cursor-pointer hover:text-electric-blue z-50">
                  {isFullScreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
                </button>
              </div>

              <div className={clsx("bg-black/80 flex items-center justify-center relative overflow-hidden", isFullScreen ? "flex-1 rounded-2xl md:mt-14 mt-12" : "aspect-video rounded-xl")}>
                <div className="absolute inset-0 bg-[url('https://images.unsplash.com/photo-1601362840469-51e4d8d58785?q=80&w=1200&auto=format&fit=crop')] bg-cover bg-center opacity-40 mix-blend-luminosity duration-1000 grayscale"></div>

                <div className="absolute top-0 left-0 w-full h-1 bg-electric-blue/50 filter blur-[2px] animate-[scan_4s_ease-in-out_infinite]" />

                <div className="relative z-10 flex flex-col items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-white/5 border border-white/10 flex items-center justify-center backdrop-blur-sm">
                    <Video className="h-5 w-5 text-electric-blue/70" />
                  </div>
                  <p className="text-xs font-medium text-electric-blue/70 font-mono tracking-widest text-center px-4">CONNECTING TO STREAM...</p>
                </div>
              </div>
            </div>
          )}

          {/* Telemetry Placeholder */}
          {!isCancelled && (
            <div className="grid grid-cols-3 gap-3">
              <div className="bg-white/5 border border-white/10 backdrop-blur-xl rounded-2xl p-4 flex flex-col items-center justify-center gap-1">
                <Thermometer className="h-4 w-4 text-electric-blue mb-1" />
                <span className="text-2xl font-light text-white">22<span className="text-sm text-gray-500">°C</span></span>
                <span className="text-[10px] text-gray-500 uppercase tracking-widest">Temp</span>
              </div>
              <div className="bg-white/5 border border-white/10 backdrop-blur-xl rounded-2xl p-4 flex flex-col items-center justify-center gap-1">
                <Droplets className="h-4 w-4 text-electric-blue mb-1" />
                <span className="text-2xl font-light text-white">45<span className="text-sm text-gray-500">%</span></span>
                <span className="text-[10px] text-gray-500 uppercase tracking-widest">Humidity</span>
              </div>
              <div className="bg-white/5 border border-emerald-500/20 backdrop-blur-xl rounded-2xl p-4 flex flex-col items-center justify-center gap-1">
                <Wind className="h-4 w-4 text-emerald-400 mb-1" />
                <span className="text-2xl font-light text-white">12<span className="text-sm text-gray-500">μg</span></span>
                <span className="text-[10px] text-gray-500 uppercase tracking-widest">PM2.5</span>
              </div>
            </div>
          )}

          {/* Progress */}
          <div className={cardClass}>
            <h2 className="font-medium text-gray-200 mb-5 tracking-wide text-sm uppercase">Progress</h2>
            <JobStatusFlow status={job.status} theme="dark" />
          </div>

          {/* Vehicle info */}
          <div className={cardClass}>
            <h2 className="font-medium text-gray-200 mb-4 tracking-wide text-sm flex items-center gap-2 uppercase">
              <Car className="h-4 w-4 text-electric-blue" />
              Your Vehicle
            </h2>
            <div className="space-y-3 text-sm">
              {job.car_model && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Model</span>
                  <span className="font-medium text-white">{job.car_model}</span>
                </div>
              )}
              {job.car_plate && (
                <div className="flex justify-between items-center">
                  <span className="text-gray-400">Plate</span>
                  <span className="font-mono font-medium text-electric-blue bg-electric-blue/10 px-2 py-0.5 rounded-md border border-electric-blue/20">{job.car_plate}</span>
                </div>
              )}
              <div className="flex justify-between items-center">
                <span className="text-gray-400">Service</span>
                <span className="font-medium text-white">{job.work_type}</span>
              </div>
            </div>
          </div>

          {/* Times */}
          <div className={cardClass}>
            <h2 className="font-medium text-gray-200 mb-4 tracking-wide text-sm flex items-center gap-2 uppercase">
              <Clock className="h-4 w-4 text-electric-blue" />
              Timing
            </h2>
            <div className="space-y-3 text-sm">
              {job.scheduled_start_time && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Scheduled</span>
                  <span className="font-medium text-white">{formatDate(job.scheduled_start_time)}</span>
                </div>
              )}
              {job.actual_start_time && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Started</span>
                  <span className="font-medium text-white">{formatDate(job.actual_start_time)}</span>
                </div>
              )}
              {job.estimated_end_time && !isComplete && !isCancelled && (
                <div className="flex justify-between">
                  <span className="text-gray-400">Est. Completion</span>
                  <span className="font-medium text-white">{formatDate(job.estimated_end_time)}</span>
                </div>
              )}
              {remaining != null && !isComplete && !isCancelled && (
                <div className="flex justify-between bg-electric-blue/10 border border-electric-blue/20 -mx-3 px-3 py-2 rounded-xl mt-3 items-center">
                  <span className="text-gray-300 font-medium">Time Remaining</span>
                  <span className="text-electric-blue font-bold tracking-wider">
                    {remaining === 0 ? 'Almost done!' : formatDurationMinutes(remaining)}
                  </span>
                </div>
              )}
            </div>
          </div>

          {/* Location */}
          {job.pit_display_name && (
            <div className={cardClass}>
              <h2 className="font-medium text-gray-200 mb-3 tracking-wide text-sm flex items-center gap-2 uppercase">
                <MapPin className="h-4 w-4 text-electric-blue" />
                Location
              </h2>
              <p className="text-sm text-gray-300">{job.pit_display_name}</p>
            </div>
          )}

          <p className="text-center text-xs text-gray-600 pb-6 pt-4 font-mono uppercase tracking-widest">
            Data auto-refreshes every 60s
          </p>
        </div>
      </div>
      <style>{`
        @keyframes scan {
          0%, 100% {
            transform: translateY(-100%);
            opacity: 0;
          }
          10%, 90% {
            opacity: 1;
          }
          50% {
            transform: translateY(200px);
          }
        }
      `}</style>
    </div>
  )
}

