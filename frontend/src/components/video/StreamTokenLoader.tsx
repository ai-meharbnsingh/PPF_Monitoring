import { useEffect, useState } from 'react'
import { VideoPlayer } from './VideoPlayer'
import { streamsApi } from '@/api/streams'
import type { StreamTokenResponse } from '@/types'

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

  useEffect(() => {
    if (!cameraIsOnline) return

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
      }
    }
    void fetchToken()
    return () => { cancelled = true }
  }, [pitId, cameraIsOnline])

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
