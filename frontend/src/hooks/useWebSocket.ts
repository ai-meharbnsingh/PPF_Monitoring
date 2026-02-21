import { useEffect } from 'react'
import toast from 'react-hot-toast'
import { useAppDispatch, useAppSelector } from './useAppDispatch'
import { wsService } from '@/services/websocket'
import { updateSensorData, deviceWentOffline, deviceCameOnline } from '@/store/slices/pitsSlice'
import { jobStatusUpdated } from '@/store/slices/jobsSlice'
import { newAlertReceived } from '@/store/slices/alertsSlice'
import { updateDeviceOnlineStatus } from '@/store/slices/devicesSlice'
import type {
  WsSensorUpdateEvent,
  WsJobStatusEvent,
  WsAlertEvent,
  WsDeviceOfflineEvent,
  WsDeviceOnlineEvent,
} from '@/types/websocket'

/**
 * Called once in AppLayout.
 * Connects the WebSocket service and wires all server events to Redux.
 */
export function useWebSocket() {
  const dispatch = useAppDispatch()
  const { token, user } = useAppSelector((s) => s.auth)

  useEffect(() => {
    if (!token || !user?.workshop_id) return

    // Connect (noop if already connected with same token)
    wsService.connect(token, user.workshop_id)

    // ── Event handlers ──────────────────────────────────────────────────────

    const unsubSensor = wsService.on('sensor_update', (msg) => {
      const e = msg as WsSensorUpdateEvent
      dispatch(updateSensorData({ pit_id: e.pit_id, data: e.data }))
    })

    const unsubJob = wsService.on('job_status', (msg) => {
      const e = msg as WsJobStatusEvent
      dispatch(
        jobStatusUpdated({
          job_id: e.job_id,
          pit_id: e.pit_id,
          new_status: e.data.new_status,
          previous_status: e.data.previous_status,
        }),
      )
    })

    const unsubAlert = wsService.on('alert', (msg) => {
      const e = msg as WsAlertEvent
      dispatch(newAlertReceived({ ...e.data, pit_id: e.pit_id }))
      toast.error(e.data.message, {
        duration: 6000,
        id: `alert-${e.data.alert_id}`,
      })
    })

    const unsubOffline = wsService.on('device_offline', (msg) => {
      const e = msg as WsDeviceOfflineEvent
      dispatch(deviceWentOffline({ pit_id: e.pit_id, device_id: e.data.device_id }))
      dispatch(updateDeviceOnlineStatus({ device_id: e.data.device_id, is_online: false }))
    })

    const unsubOnline = wsService.on('device_online', (msg) => {
      const e = msg as WsDeviceOnlineEvent
      dispatch(deviceCameOnline({ pit_id: e.pit_id, device_id: e.data.device_id }))
      dispatch(updateDeviceOnlineStatus({ device_id: e.data.device_id, is_online: true }))
    })

    return () => {
      unsubSensor()
      unsubJob()
      unsubAlert()
      unsubOffline()
      unsubOnline()
      // Don't disconnect on unmount — AppLayout stays mounted for the whole session
    }
  }, [token, user?.workshop_id, dispatch])
}
