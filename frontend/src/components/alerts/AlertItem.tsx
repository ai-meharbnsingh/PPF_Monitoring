import { Check, AlertTriangle } from 'lucide-react'
import type { AlertResponse } from '@/types/alert'
import { AlertSeverityBadge } from './AlertSeverityBadge'
import { formatRelative } from '@/utils/formatters'
import { toTitleCase } from '@/utils/formatters'
import { Button } from '@/components/ui/Button'

interface AlertItemProps {
  alert: AlertResponse
  onAcknowledge: (id: number) => void
  isAcknowledging?: boolean
}

export function AlertItem({ alert, onAcknowledge, isAcknowledging }: AlertItemProps) {
  return (
    <div className="flex items-start gap-3 p-3 rounded-lg border border-gray-100 bg-white hover:bg-gray-50 transition-colors">
      <div className="mt-0.5 shrink-0">
        <AlertTriangle
          className={
            alert.severity === 'critical'
              ? 'h-4 w-4 text-red-500'
              : alert.severity === 'warning'
              ? 'h-4 w-4 text-amber-500'
              : 'h-4 w-4 text-blue-500'
          }
        />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2 mb-0.5">
          <AlertSeverityBadge severity={alert.severity} />
          <span className="text-xs text-gray-400">{formatRelative(alert.created_at)}</span>
        </div>
        <p className="text-sm text-gray-800">{alert.message}</p>
        {alert.trigger_value != null && alert.threshold_value != null && (
          <p className="text-xs text-gray-500 mt-0.5">
            Value: {alert.trigger_value.toFixed(1)} / Threshold: {alert.threshold_value.toFixed(1)}
          </p>
        )}
        <p className="text-xs text-gray-400 mt-0.5">{toTitleCase(alert.alert_type)}</p>
      </div>
      {!alert.is_acknowledged ? (
        <Button
          size="sm"
          variant="ghost"
          isLoading={isAcknowledging}
          onClick={() => onAcknowledge(alert.id)}
          title="Acknowledge"
          className="shrink-0"
        >
          <Check className="h-3.5 w-3.5" />
        </Button>
      ) : (
        <span className="shrink-0 text-xs text-gray-400 mt-1">Ack</span>
      )}
    </div>
  )
}
