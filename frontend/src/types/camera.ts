/**
 * Camera Type Definitions
 */

export interface StreamUrls {
  webrtc?: {
    main?: string
    sub?: string
  }
  hls?: {
    main?: string
    sub?: string
  }
  rtsp?: {
    main?: string
    sub?: string
  }
  rtmp?: {
    main?: string
    sub?: string
  }
}

export interface CameraCapabilities {
  resolutions?: string[]
  protocols?: string[]
  has_audio?: boolean
  has_ptz?: boolean
}

export interface MediaMTXConfig {
  host: string
  ports: {
    webrtc?: number
    hls?: number
    rtsp?: number
    rtmp?: number
  }
  paths: string[]
}

export interface Camera {
  id: number
  device_id: string
  name: string
  description?: string
  camera_type: string
  model?: string
  manufacturer?: string
  ip_address: string
  hostname?: string
  port: number
  stream_urls?: StreamUrls
  mediamtx_config?: MediaMTXConfig
  status: 'pending' | 'online' | 'offline' | 'error'
  is_online: boolean
  is_assigned: boolean
  has_ptz: boolean
  has_audio: boolean
  last_seen?: string
  discovered_at?: string
  created_at?: string
  workshop_id: number
  pit_id?: number
  pit_name?: string
  primary_stream_url?: string
}

export interface CameraAssignmentRequest {
  pit_id: number
  custom_name?: string
}

export interface CameraNotification {
  type: 'camera_discovered' | 'camera_online' | 'camera_offline' | 'camera_assigned'
  camera: Camera
  message: string
  timestamp: string
}

export interface CameraState {
  cameras: Camera[]
  discoveredCameras: Camera[]
  selectedCamera: Camera | null
  loading: boolean
  error: string | null
}
