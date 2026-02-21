// ─── Stream token response ────────────────────────────────────────────────────
export interface StreamTokenResponse {
  pit_id: number
  stream_token: string
  expires_at: string
  rtsp_url: string
  webrtc_url: string
  hls_url: string
}

// ─── Stream status ────────────────────────────────────────────────────────────
export interface PitStreamStatus {
  pit_id: number
  camera_is_online: boolean
  camera_ip: string | null
  camera_model: string | null
  camera_last_seen: string | null
  rtsp_path: string | null
}
