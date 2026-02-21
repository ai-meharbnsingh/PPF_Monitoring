import type { WsClientAction, WsServerEvent } from '@/types/websocket'

type WsEventHandler = (event: WsServerEvent) => void

/**
 * WebSocketService — singleton class
 * Handles connection, ping/pong keepalive, exponential backoff reconnect,
 * and a simple pub/sub for WS server events.
 */
class WebSocketService {
  private ws: WebSocket | null = null
  private token: string | null = null
  private workshopId: number | null = null

  // Reconnect state
  private reconnectAttempts = 0
  private readonly maxReconnectAttempts = 10
  private readonly baseDelay = 1000    // 1 second
  private readonly maxDelay = 30_000  // 30 seconds
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null

  // Ping keepalive
  private pingTimer: ReturnType<typeof setInterval> | null = null
  private readonly pingIntervalMs = 25_000

  // Event handlers: event name → set of handlers
  private handlers: Map<string, Set<WsEventHandler>> = new Map()

  // ── Public API ──────────────────────────────────────────────────────────────

  connect(token: string, workshopId: number): void {
    this.token = token
    this.workshopId = workshopId
    this.reconnectAttempts = 0
    this._open()
  }

  /**
   * Subscribe to a specific event type.
   * Use '*' to subscribe to all events.
   * Returns an unsubscribe function.
   */
  on(event: string, handler: WsEventHandler): () => void {
    if (!this.handlers.has(event)) {
      this.handlers.set(event, new Set())
    }
    this.handlers.get(event)!.add(handler)
    return () => {
      this.handlers.get(event)?.delete(handler)
    }
  }

  send(action: WsClientAction): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(action))
    }
  }

  disconnect(): void {
    // Stop reconnect
    this.reconnectAttempts = this.maxReconnectAttempts
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this._clearPing()
    this.ws?.close(1000, 'user logout')
    this.ws = null
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }

  // ── Private helpers ─────────────────────────────────────────────────────────

  private _open(): void {
    if (!this.token) return

    const wsBase = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000/ws'
    const url = `${wsBase}?token=${this.token}`

    try {
      this.ws = new WebSocket(url)
    } catch (err) {
      console.error('[WS] Failed to create WebSocket:', err)
      this._scheduleReconnect()
      return
    }

    this.ws.onopen = () => {
      console.log('[WS] Connected')
      this.reconnectAttempts = 0
      // Subscribe to the workshop
      if (this.workshopId != null) {
        this.send({ action: 'subscribe_workshop', workshop_id: this.workshopId })
      }
      // Start ping
      this._startPing()
    }

    this.ws.onmessage = (evt: MessageEvent) => {
      try {
        const msg = JSON.parse(evt.data as string) as WsServerEvent
        // Dispatch to event-specific handlers
        this.handlers.get(msg.event)?.forEach((h) => h(msg))
        // Dispatch to wildcard handlers
        this.handlers.get('*')?.forEach((h) => h(msg))
      } catch {
        // Ignore malformed messages
      }
    }

    this.ws.onerror = () => {
      console.warn('[WS] Error — closing')
      this.ws?.close()
    }

    this.ws.onclose = (evt: CloseEvent) => {
      console.warn(`[WS] Closed (code=${evt.code})`)
      this._clearPing()
      // Don't reconnect on explicit logout close (1000)
      if (evt.code !== 1000) {
        this._scheduleReconnect()
      }
    }
  }

  private _scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error('[WS] Max reconnect attempts reached')
      return
    }
    const delay = Math.min(
      this.baseDelay * Math.pow(2, this.reconnectAttempts),
      this.maxDelay,
    )
    this.reconnectAttempts++
    console.log(`[WS] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`)
    this.reconnectTimer = setTimeout(() => this._open(), delay)
  }

  private _startPing(): void {
    this._clearPing()
    this.pingTimer = setInterval(() => {
      this.send({ action: 'ping' })
    }, this.pingIntervalMs)
  }

  private _clearPing(): void {
    if (this.pingTimer) {
      clearInterval(this.pingTimer)
      this.pingTimer = null
    }
  }
}

// Export singleton
export const wsService = new WebSocketService()
