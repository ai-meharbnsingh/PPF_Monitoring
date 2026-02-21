import { useState } from 'react'
import { Modal } from '@/components/ui/Modal'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { Input } from '@/components/ui/Input'
import { devicesApi } from '@/api/devices'
import type { DeviceResponse } from '@/types/device'
import type { DeviceCommand } from '@/types/common'
import toast from 'react-hot-toast'

interface DeviceCommandModalProps {
  isOpen: boolean
  onClose: () => void
  device: DeviceResponse | null
}

const COMMAND_OPTIONS: { value: DeviceCommand; label: string }[] = [
  { value: 'ENABLE', label: 'Enable Device' },
  { value: 'DISABLE', label: 'Disable Device' },
  { value: 'RESTART', label: 'Restart Device' },
  { value: 'SET_INTERVAL', label: 'Set Report Interval' },
]

export function DeviceCommandModal({ isOpen, onClose, device }: DeviceCommandModalProps) {
  const [command, setCommand] = useState<DeviceCommand>('RESTART')
  const [interval, setInterval] = useState('30')
  const [reason, setReason] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSend = async () => {
    if (!device) return
    setLoading(true)
    try {
      const payload =
        command === 'SET_INTERVAL'
          ? { interval_seconds: Number(interval) }
          : undefined

      await devicesApi.sendCommand(device.device_id, {
        command,
        reason: reason || undefined,
        payload,
      })
      toast.success(`Command "${command}" sent to ${device.device_id}`)
      onClose()
    } catch {
      toast.error('Failed to send command')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={`Send Command — ${device?.device_id ?? ''}`}
      size="sm"
    >
      <div className="space-y-4">
        <Select
          label="Command"
          value={command}
          options={COMMAND_OPTIONS}
          onChange={(e) => setCommand(e.target.value as DeviceCommand)}
        />

        {command === 'SET_INTERVAL' && (
          <Input
            label="Interval (seconds)"
            type="number"
            min="5"
            max="3600"
            value={interval}
            onChange={(e) => setInterval(e.target.value)}
          />
        )}

        <Input
          label="Reason (optional)"
          placeholder="Why are you sending this command?"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
        />

        <div className="flex justify-end gap-3 pt-1">
          <Button variant="secondary" onClick={onClose}>
            Cancel
          </Button>
          <Button
            variant={command === 'DISABLE' ? 'danger' : 'primary'}
            isLoading={loading}
            onClick={handleSend}
          >
            Send
          </Button>
        </div>
      </div>
    </Modal>
  )
}
