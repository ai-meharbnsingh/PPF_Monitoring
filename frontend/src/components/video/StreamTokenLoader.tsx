import { VideoPlayer } from './VideoPlayer'
import { useVideoStream } from '@/hooks/useVideoStream'
import { Spinner } from '@/components/ui/Spinner'
import { Button } from '@/components/ui/Button'
import { RefreshCw } from 'lucide-react'

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
  const { streamData, isLoading, error, refresh } = useVideoStream(
    cameraIsOnline ? pitId : null,
  )

  if (!cameraIsOnline) {
    return (
      <VideoPlayer
        webrtcUrl=""
        hlsUrl=""
        pitName={pitName}
        isOnline={false}
        cameraLastSeen={cameraLastSeen}
        className={className}
      />
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center bg-gray-900 rounded-xl p-8 min-h-[200px]">
        <Spinner label="Loading stream…" />
      </div>
    )
  }

  if (error || !streamData) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 bg-gray-900 rounded-xl p-8 text-center">
        <p className="text-sm text-gray-400">{error ?? 'Stream unavailable'}</p>
        <Button variant="ghost" size="sm" onClick={refresh} leftIcon={<RefreshCw className="h-3.5 w-3.5" />}>
          Retry
        </Button>
      </div>
    )
  }

  return (
    <VideoPlayer
      webrtcUrl={streamData.webrtc_url}
      hlsUrl={streamData.hls_url}
      pitName={pitName}
      isOnline={cameraIsOnline}
      cameraLastSeen={cameraLastSeen}
      className={className}
    />
  )
}
