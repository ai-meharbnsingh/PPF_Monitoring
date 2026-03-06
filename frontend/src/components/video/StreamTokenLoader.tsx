import { useEffect, useState } from 'react'
import { VideoPlayer } from './VideoPlayer'
import { streamsApi } from '@/api/streams'
import type { StreamTokenResponse } from '@/types'
import { Loader2 } from 'lucide-react'
import { clsx } from 'clsx'

interface StreamTokenLoaderProps {
  pitId: number
  pitName?: string
  cameraIsOnline: boolean
  cameraLastSeen?: string | null
  className?: string
}

export function StreamTokenLoader({
  pitId,
  pitName,
  cameraIsOnline,
  cameraLastSeen,
  className,
}: StreamTokenLoaderProps) {
  const [webrtcUrl, setWebrtcUrl] = useState('')
  const [hlsUrl, setHlsUrl] = useState('')
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    if (!cameraIsOnline) {
      setIsLoading(false)
      return
    }

    let cancelled = false
    const fetchToken = async () => {
      try {
        const result: StreamTokenResponse = await streamsApi.getStreamToken(pitId)
        if (!cancelled) {
          setWebrtcUrl(result.webrtc_url ?? '')
          setHlsUrl(result.hls_url ?? '')
        }
      } catch {
        // Stream token fetch failed — VideoPlayer will show offline
      } finally {
        if (!cancelled) {
          setIsLoading(false)
        }
      }
    }
    void fetchToken()
    return () => { cancelled = true }
  }, [pitId, cameraIsOnline])

  // Show loading spinner while fetching token
  if (isLoading) {
    return (
      <div
        className={clsx(
          'flex flex-col items-center justify-center gap-3 bg-gray-900 rounded-xl text-center',
          className,
        )}
      >
        <Loader2 className="h-8 w-8 text-electric-blue animate-spin" />
        <p className="text-sm text-gray-400">Loading video stream...</p>
      </div>
    )
  }

  return (
    <VideoPlayer
      webrtcUrl={webrtcUrl}
      hlsUrl={hlsUrl}
      pitName={pitName}
      isOnline={cameraIsOnline}
      cameraLastSeen={cameraLastSeen}
      className={className}
    />
  )
}
