import { useEffect, useRef, useState } from 'react'
import { clsx } from 'clsx'
import { VideoOff, Wifi, Loader2, Maximize2, Minimize2 } from 'lucide-react'
import Hls from 'hls.js'
import { formatRelative } from '@/utils/formatters'

interface VideoPlayerProps {
  webrtcUrl: string
  hlsUrl: string
  pitName?: string
  isOnline: boolean
  cameraLastSeen?: string | null
  className?: string
}

type StreamProtocol = 'webrtc' | 'hls' | 'offline' | 'loading'

export function VideoPlayer({
  webrtcUrl,
  hlsUrl,
  pitName,
  isOnline,
  cameraLastSeen,
  className,
}: VideoPlayerProps) {
  const videoRef = useRef<HTMLVideoElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const hlsRef = useRef<Hls | null>(null)
  const pcRef = useRef<RTCPeerConnection | null>(null)
  const [protocol, setProtocol] = useState<StreamProtocol>('loading')
  const [error, setError] = useState<string | null>(null)
  const [isFullscreen, setIsFullscreen] = useState(false)

  // Handle fullscreen toggle
  const toggleFullscreen = async () => {
    if (!containerRef.current) return
    
    try {
      if (!document.fullscreenElement) {
        await containerRef.current.requestFullscreen()
        setIsFullscreen(true)
      } else {
        await document.exitFullscreen()
        setIsFullscreen(false)
      }
    } catch (err) {
      console.error('Fullscreen error:', err)
    }
  }

  // Listen for fullscreen change events
  useEffect(() => {
    const handleFullscreenChange = () => {
      setIsFullscreen(!!document.fullscreenElement)
    }
    document.addEventListener('fullscreenchange', handleFullscreenChange)
    return () => document.removeEventListener('fullscreenchange', handleFullscreenChange)
  }, [])

  useEffect(() => {
    console.log('VideoPlayer mounted/updated:', { webrtcUrl, hlsUrl, isOnline })
    
    if (!isOnline) {
      setProtocol('offline')
      return
    }

    setProtocol('loading')
    setError(null)

    // Try WebRTC (WHEP) first
    const tryWebRTC = async () => {
      try {
        const pc = new RTCPeerConnection({
          iceServers: [{ urls: 'stun:stun.l.google.com:19302' }],
        })
        pcRef.current = pc

        // Add receive-only transceiver
        pc.addTransceiver('video', { direction: 'recvonly' })
        pc.addTransceiver('audio', { direction: 'recvonly' })

        // Create SDP offer
        const offer = await pc.createOffer()
        await pc.setLocalDescription(offer)

        // POST SDP offer to MediaMTX WHEP endpoint
        const controller = new AbortController()
        const timeoutId = setTimeout(() => controller.abort(), 5000)

        const resp = await fetch(webrtcUrl, {
          method: 'POST',
          headers: { 'Content-Type': 'application/sdp' },
          body: pc.localDescription?.sdp,
          signal: controller.signal,
        })
        clearTimeout(timeoutId)

        if (!resp.ok) throw new Error('WHEP response not OK')
        const answerSdp = await resp.text()
        await pc.setRemoteDescription({ type: 'answer', sdp: answerSdp })

        // Attach stream when track received
        pc.ontrack = (evt) => {
          if (videoRef.current && evt.streams[0]) {
            videoRef.current.srcObject = evt.streams[0]
            setProtocol('webrtc')
          }
        }
      } catch {
        // WebRTC failed → try HLS
        pcRef.current?.close()
        pcRef.current = null
        void tryHLS()
      }
    }

    const tryHLS = async () => {
      console.log('Trying HLS with URL:', hlsUrl)
      if (!videoRef.current) return
      if (Hls.isSupported()) {
        const hls = new Hls({ enableWorker: false })
        hlsRef.current = hls
        hls.loadSource(hlsUrl)
        hls.attachMedia(videoRef.current)
        hls.on(Hls.Events.MANIFEST_PARSED, () => {
          void videoRef.current?.play().catch(() => {})
          setProtocol('hls')
        })
        hls.on(Hls.Events.ERROR, (_, data) => {
          console.error('HLS error:', data)
          if (data.fatal) {
            setError(`Video stream error: ${data.type} - ${data.details}`)
            setProtocol('offline')
          }
        })
      } else if (videoRef.current.canPlayType('application/vnd.apple.mpegurl')) {
        // Safari native HLS
        videoRef.current.src = hlsUrl
        setProtocol('hls')
      } else {
        setError('Video not supported in this browser')
        setProtocol('offline')
      }
    }

    // Skip WebRTC for Tailscale Funnel or HTTPS URLs (UDP won't work through funnel)
    // HLS works perfectly over HTTPS
    const isTailscaleFunnel = webrtcUrl.includes('ts.net') || webrtcUrl.includes('tailscale')
    const isHttpsWebRTC = webrtcUrl.startsWith('https://') && webrtcUrl.includes('/whep')
    
    if (webrtcUrl && !isTailscaleFunnel && !isHttpsWebRTC) {
      void tryWebRTC()
    } else {
      // Use HLS for funnel or if WebRTC URL is HTTPS
      console.log('Using HLS for Tailscale Funnel / HTTPS stream')
      void tryHLS()
    }

    return () => {
      // Cleanup
      hlsRef.current?.destroy()
      hlsRef.current = null
      pcRef.current?.close()
      pcRef.current = null
      if (videoRef.current) {
        videoRef.current.srcObject = null
        videoRef.current.src = ''
      }
    }
  }, [webrtcUrl, hlsUrl, isOnline])

  if (!isOnline || protocol === 'offline') {
    return (
      <div
        className={clsx(
          'flex flex-col items-center justify-center gap-3 bg-gray-900 rounded-xl text-center p-8',
          className,
        )}
      >
        <VideoOff className="h-10 w-10 text-gray-500" />
        <div>
          <p className="text-sm text-gray-400 font-medium">Camera Offline</p>
          {cameraLastSeen && (
            <p className="text-xs text-gray-600 mt-0.5">
              Last seen {formatRelative(cameraLastSeen)}
            </p>
          )}
        </div>
        {error && <p className="text-xs text-red-400">{error}</p>}
      </div>
    )
  }

  return (
    <div 
      ref={containerRef}
      className={clsx('relative bg-black rounded-xl overflow-hidden cursor-pointer group', className)}
      onClick={toggleFullscreen}
    >
      {/* Loading overlay */}
      {protocol === 'loading' && (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
          <Loader2 className="h-8 w-8 animate-spin text-gray-400" />
        </div>
      )}

      {/* Protocol badge */}
      {protocol !== 'loading' && (
        <div className="absolute top-2 right-2 z-10 flex items-center gap-1 bg-black/60 text-white text-[10px] font-medium px-2 py-0.5 rounded-full">
          <Wifi className="h-3 w-3" />
          Live ({protocol.toUpperCase()})
        </div>
      )}

      {pitName && (
        <div className="absolute top-2 left-2 z-10 bg-black/60 text-white text-[10px] px-2 py-0.5 rounded-full">
          {pitName}
        </div>
      )}

      {/* Fullscreen button - shows on hover/tap */}
      <div className="absolute bottom-2 right-2 z-20 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
        <button
          onClick={(e) => {
            e.stopPropagation()
            void toggleFullscreen()
          }}
          className="flex items-center justify-center w-10 h-10 bg-black/60 hover:bg-black/80 text-white rounded-full backdrop-blur-sm transition-colors"
          aria-label={isFullscreen ? 'Exit fullscreen' : 'Enter fullscreen'}
        >
          {isFullscreen ? (
            <Minimize2 className="h-5 w-5" />
          ) : (
            <Maximize2 className="h-5 w-5" />
          )}
        </button>
      </div>

      {/* Click hint for mobile */}
      <div className="absolute inset-0 flex items-center justify-center z-10 opacity-0 group-active:opacity-100 transition-opacity duration-200 pointer-events-none">
        <div className="bg-black/50 text-white text-xs px-3 py-1.5 rounded-full backdrop-blur-sm">
          Tap for fullscreen
        </div>
      </div>

      <video
        ref={videoRef}
        autoPlay
        muted
        playsInline
        className="w-full h-full object-contain"
        style={{ minHeight: '200px' }}
      />
    </div>
  )
}
