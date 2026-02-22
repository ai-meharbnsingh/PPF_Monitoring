import { clsx } from 'clsx'
import Webcam from 'react-webcam'
import { VideoPlayer } from './VideoPlayer'

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

  // Demo override: Use react-webcam instead of actual Stream logic
  return (
    <div className={clsx('relative w-full h-full bg-black flex items-center justify-center overflow-hidden', className)}>
      <Webcam
        audio={false}
        className="object-cover w-full h-full opacity-90"
        videoConstraints={{
          facingMode: "environment"
        }}
      />
    </div>
  )
}
