import { Bell } from 'lucide-react'
import { useAppDispatch } from '@/hooks/useAppDispatch'
import { setPanelOpen } from '@/store/slices/alertsSlice'
import { clsx } from 'clsx'

interface AlertBellProps {
  unreadCount: number
}

export function AlertBell({ unreadCount }: AlertBellProps) {
  const dispatch = useAppDispatch()

  return (
    <button
      onClick={() => dispatch(setPanelOpen(true))}
      className="relative p-2 rounded-lg text-gray-500 hover:text-gray-900 hover:bg-gray-100 transition-colors"
      title="Alerts"
    >
      <Bell className={clsx('h-5 w-5', unreadCount > 0 && 'text-red-500')} />
      {unreadCount > 0 && (
        <span className="absolute top-0.5 right-0.5 min-w-[18px] h-[18px] bg-red-500 text-white text-[10px] font-bold rounded-full flex items-center justify-center px-1 animate-pulse">
          {unreadCount > 99 ? '99+' : unreadCount}
        </span>
      )}
    </button>
  )
}
