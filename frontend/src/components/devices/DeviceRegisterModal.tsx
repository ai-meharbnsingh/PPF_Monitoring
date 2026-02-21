import { useState } from 'react'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Button } from '@/components/ui/Button'
import { devicesApi } from '@/api/devices'
import { useAppSelector } from '@/hooks/useAppDispatch'
import type { SensorTypeCode } from '@/types/common'
import toast from 'react-hot-toast'

interface DeviceRegisterModalProps {
  isOpen: boolean
  onClose: () => void
  onRegistered: () => void
}

const SENSOR_OPTIONS: { value: SensorTypeCode; label: string }[] = [
  { value: 'DHT22', label: 'DHT22 (Temp + Humidity)' },
  { value: 'BME680', label: 'BME680 (Temp + Humidity + IAQ)' },
]

const AQ_SENSOR_OPTIONS = [
  { value: '', label: 'None' },
  { value: 'PMS5003', label: 'PMS5003 (Particulate Matter)' },
]

const PIT_OPTION_NONE = { value: '', label: '— Select Pit —' }

export function DeviceRegisterModal({ isOpen, onClose, onRegistered }: DeviceRegisterModalProps) {
  const pits = useAppSelector((s) => s.pits.pits)
  const workshopId = useAppSelector((s) => s.auth.user?.workshop_id)
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<{
    device_id: string
    license_key: string
  } | null>(null)

  const [form, setForm] = useState({
    device_id: '',
    pit_id: '',
    primary: 'DHT22' as SensorTypeCode,
    air_quality: '' as SensorTypeCode | '',
    interval: '30',
    mac: '',
  })

  const handleChange = (field: keyof typeof form) => (
    e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>,
  ) => setForm((f) => ({ ...f, [field]: e.target.value }))

  const handleRegister = async () => {
    if (!form.device_id || !form.pit_id || !workshopId) {
      toast.error('Device ID and Pit are required')
      return
    }
    setLoading(true)
    try {
      const resp = await devicesApi.register(workshopId, {
        device_id: form.device_id,
        pit_id: Number(form.pit_id),
        primary_sensor_type_code: form.primary,
        air_quality_sensor_type_code: (form.air_quality as SensorTypeCode) || undefined,
        report_interval_seconds: Number(form.interval),
        mac_address: form.mac || undefined,
      })
      setResult({ device_id: resp.device_id, license_key: resp.license_key })
      onRegistered()
    } catch {
      toast.error('Failed to register device')
    } finally {
      setLoading(false)
    }
  }

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Register New Device" size="md">
      {result ? (
        <div className="space-y-4">
          <div className="p-4 bg-green-50 border border-green-200 rounded-xl">
            <p className="font-semibold text-green-800 mb-2">Device Registered!</p>
            <p className="text-sm text-gray-700">
              <strong>Device ID:</strong>{' '}
              <span className="font-mono">{result.device_id}</span>
            </p>
            <p className="text-sm text-gray-700 mt-1">
              <strong>License Key:</strong>{' '}
              <span className="font-mono">{result.license_key}</span>
            </p>
          </div>
          <p className="text-xs text-gray-500">
            Flash this license key to your ESP32 firmware. Keep it secret.
          </p>
          <Button className="w-full" onClick={() => { setResult(null); onClose() }}>
            Done
          </Button>
        </div>
      ) : (
        <div className="space-y-4">
          <Input
            label="Device ID *"
            placeholder="ESP32-AABBCCDDEEFF"
            value={form.device_id}
            onChange={handleChange('device_id')}
          />
          <Select
            label="Pit / Bay *"
            value={form.pit_id}
            options={[
              PIT_OPTION_NONE,
              ...pits.map((p) => ({ value: String(p.id), label: p.name })),
            ]}
            onChange={handleChange('pit_id')}
          />
          <Select
            label="Primary Sensor"
            value={form.primary}
            options={SENSOR_OPTIONS}
            onChange={handleChange('primary')}
          />
          <Select
            label="Air Quality Sensor"
            value={form.air_quality}
            options={AQ_SENSOR_OPTIONS}
            onChange={handleChange('air_quality')}
          />
          <Input
            label="Report Interval (seconds)"
            type="number"
            min="5"
            max="3600"
            value={form.interval}
            onChange={handleChange('interval')}
          />
          <Input
            label="MAC Address (optional)"
            placeholder="AA:BB:CC:DD:EE:FF"
            value={form.mac}
            onChange={handleChange('mac')}
          />
          <div className="flex justify-end gap-3 pt-1">
            <Button variant="secondary" onClick={onClose}>Cancel</Button>
            <Button isLoading={loading} onClick={handleRegister}>Register</Button>
          </div>
        </div>
      )}
    </Modal>
  )
}
