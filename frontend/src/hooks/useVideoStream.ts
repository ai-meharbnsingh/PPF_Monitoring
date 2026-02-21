import { useState, useEffect, useRef, useCallback } from 'react'
import { streamsApi } from '@/api/streams'
import type { StreamTokenResponse } from '@/types/stream'
import { parseISO, subMinutes } from 'date-fns'

interface UseVideoStreamResult {
  streamData: StreamTokenResponse | null
  isLoading: boolean
  error: string | null
  refresh: () => void
}

export function useVideoStream(pitId: number | null): UseVideoStreamResult {
  const [streamData, setStreamData] = useState<StreamTokenResponse | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const fetchToken = useCallback(async () => {
    if (!pitId) return
    setIsLoading(true)
    setError(null)
    try {
      const data = await streamsApi.getStreamToken(pitId)
      setStreamData(data)

      // Schedule refresh 2 minutes before token expires
      const expiresAt = parseISO(data.expires_at)
      const refreshAt = subMinutes(expiresAt, 2)
      const msUntilRefresh = refreshAt.getTime() - Date.now()
      if (msUntilRefresh > 0) {
        if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
        refreshTimerRef.current = setTimeout(() => void fetchToken(), msUntilRefresh)
      }
    } catch {
      setError('Failed to load video stream')
    } finally {
      setIsLoading(false)
    }
  }, [pitId])

  useEffect(() => {
    if (pitId) {
      void fetchToken()
    }
    return () => {
      if (refreshTimerRef.current) clearTimeout(refreshTimerRef.current)
    }
  }, [pitId, fetchToken])

  return { streamData, isLoading, error, refresh: fetchToken }
}
