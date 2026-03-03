/**
 * Camera Stream Player Component
 * Plays video streams from cameras using WebRTC or HLS
 */

import { useEffect, useRef, useState } from 'react'
import Hls from 'hls.js'
import { Loader2, VideoOff, RefreshCw } from 'lucide-react'

interface CameraStreamPlayerProps {
  streamUrl: string
  type?: 'webrtc' | 'hls' | 'auto'
  className?: string
  muted?: boolean
  autoPlay?: boolean
  controls?: boolean
}

export function CameraStreamPlayer({
  streamUrl,
  type = 'auto',
  className = '',
  muted = true,
  autoPlay = true,
  controls = true
}: CameraStreamPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const hlsRef = useRef<Hls | null>(null)
  const pcRef = useRef<RTCPeerConnection | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [retryCount, setRetryCount] = useState(0)

  // Detect stream type from URL
  const detectStreamType = (): 'webrtc' | 'hls' => {
    if (type !== 'auto') return type
    if (streamUrl.includes('/whep') || streamUrl.includes('webrtc')) return 'webrtc'
    if (streamUrl.includes('.m3u8') || streamUrl.includes('/hls')) return 'hls'
    if (streamUrl.includes('rtsp://')) {
      console.warn('RTSP not supported in browser, trying HLS fallback')
      return 'hls'
    }
    return 'webrtc' // Default to WebRTC
  }

  const cleanup = () => {
    // Cleanup HLS
    if (hlsRef.current) {
      hlsRef.current.destroy()
      hlsRef.current = null
    }
    // Cleanup WebRTC
    if (pcRef.current) {
      pcRef.current.close()
      pcRef.current = null
    }
    // Stop video
    if (videoRef.current) {
      videoRef.current.src = ''
      videoRef.current.load()
    }
  }

  const startStream = async () => {
    if (!streamUrl || !videoRef.current) return

    setLoading(true)
    setError(null)

    const streamType = detectStreamType()

    try {
      if (streamType === 'webrtc') {
        await startWebRTC()
      } else {
        await startHLS()
      }
    } catch (err: any) {
      console.error('Stream error:', err)
      setError(err.message || 'Failed to start stream')
      setLoading(false)
    }
  }

  const startWebRTC = async () => {
    const video = videoRef.current
    if (!video) return

    // Create peer connection
    const pc = new RTCPeerConnection({
      iceServers: [
        { urls: 'stun:stun.l.google.com:19302' },
        { urls: 'stun:stun1.l.google.com:19302' }
      ]
    })
    pcRef.current = pc

    // Add transceiver for video
    pc.addTransceiver('video', { direction: 'recvonly' })

    // Handle incoming stream
    pc.ontrack = (event) => {
      if (event.streams && event.streams[0]) {
        video.srcObject = event.streams[0]
        setLoading(false)
      }
    }

    // Create offer
    const offer = await pc.createOffer()
    await pc.setLocalDescription(offer)

    // Wait for ICE gathering
    await new Promise<void>((resolve) => {
      if (pc.iceGatheringState === 'complete') {
        resolve()
      } else {
        const checkState = () => {
          if (pc.iceGatheringState === 'complete') {
            pc.removeEventListener('icegatheringstatechange', checkState)
            resolve()
          }
        }
        pc.addEventListener('icegatheringstatechange', checkState)
        // Timeout after 3 seconds
        setTimeout(resolve, 3000)
      }
    })

    // Send offer to WHEP endpoint
    const response = await fetch(streamUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/sdp' },
      body: pc.localDescription?.sdp
    })

    if (!response.ok) {
      throw new Error(`WHEP error: ${response.status}`)
    }

    // Set remote description
    const answerSdp = await response.text()
    await pc.setRemoteDescription({
      type: 'answer',
      sdp: answerSdp
    })

    // Start playing
    video.play().catch(console.error)
  }

  const startHLS = async () => {
    const video = videoRef.current
    if (!video) return

    // Convert WebRTC URL to HLS if needed
    let hlsUrl = streamUrl
    if (streamUrl.includes('/whep')) {
      hlsUrl = streamUrl.replace('/whep', '/index.m3u8').replace(':8889', ':8888')
    }

    if (Hls.isSupported()) {
      const hls = new Hls({
        enableWorker: true,
        lowLatencyMode: true,
        backBufferLength: 90
      })
      hlsRef.current = hls

      hls.on(Hls.Events.MANIFEST_PARSED, () => {
        setLoading(false)
        video.play().catch(console.error)
      })

      hls.on(Hls.Events.ERROR, (event, data) => {
        console.error('HLS error:', data)
        if (data.fatal) {
          setError('Stream error')
          setLoading(false)
        }
      })

      hls.loadSource(hlsUrl)
      hls.attachMedia(video)
    } else if (video.canPlayType('application/vnd.apple.mpegurl')) {
      // Native HLS support (Safari)
      video.src = hlsUrl
      video.addEventListener('loadedmetadata', () => {
        setLoading(false)
        video.play().catch(console.error)
      })
    } else {
      throw new Error('HLS not supported in this browser')
    }
  }

  // Start stream on mount and when URL changes
  useEffect(() => {
    startStream()
    return cleanup
  }, [streamUrl, retryCount])

  const handleRetry = () => {
    cleanup()
    setRetryCount(c => c + 1)
  }

  return (
    <div className={`relative bg-black rounded-lg overflow-hidden ${className}`}>
      <video
        ref={videoRef}
        className="w-full h-full object-contain"
        muted={muted}
        autoPlay={autoPlay}
        controls={controls}
        playsInline
      />

      {/* Loading Overlay */}
      {loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/50">
          <Loader2 className="w-10 h-10 text-white animate-spin" />
          <span className="text-white text-sm mt-2">Connecting...</span>
        </div>
      )}

      {/* Error Overlay */}
      {error && !loading && (
        <div className="absolute inset-0 flex flex-col items-center justify-center bg-black/80">
          <VideoOff className="w-12 h-12 text-red-500 mb-2" />
          <span className="text-white text-sm">{error}</span>
          <button
            onClick={handleRetry}
            className="mt-3 flex items-center gap-1 px-3 py-1 bg-white/20 hover:bg-white/30 rounded text-white text-sm"
          >
            <RefreshCw className="w-4 h-4" />
            Retry
          </button>
        </div>
      )}
    </div>
  )
}

export default CameraStreamPlayer
