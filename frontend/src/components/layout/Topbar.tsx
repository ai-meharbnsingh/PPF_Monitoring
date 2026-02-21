import { Menu, LogOut } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { useAppSelector } from '@/hooks/useAppDispatch'
import { AlertBell } from '@/components/alerts/AlertBell'

interface TopbarProps {
  onMenuClick: () => void
}

export function Topbar({ onMenuClick }: TopbarProps) {
  const navigate = useNavigate()
  const { logout, user } = useAuth()
  const unreadCount = useAppSelector((s) => s.alerts.unreadCount)

  const handleLogout = async () => {
    await logout()
    navigate('/login')
  }

  return (
    <header className="sticky top-0 z-10 h-16 bg-white border-b border-gray-200 flex items-center px-4 gap-4">
      {/* Hamburger — mobile only */}
      <button
        onClick={onMenuClick}
        className="p-2 rounded-lg text-gray-500 hover:bg-gray-100 lg:hidden"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Alert bell */}
      <AlertBell unreadCount={unreadCount} />

      {/* User menu */}
      <div className="flex items-center gap-3">
        <span className="hidden sm:block text-sm text-gray-600">
          {user?.first_name ?? user?.username}
        </span>
        <button
          onClick={handleLogout}
          title="Log out"
          className="p-2 rounded-lg text-gray-400 hover:text-red-600 hover:bg-red-50 transition-colors"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  )
}
