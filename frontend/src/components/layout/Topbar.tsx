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
    <header
      className="sticky top-0 z-10 h-16 flex items-center px-4 gap-4 border-b border-white/[0.08]"
      style={{ background: 'rgba(18,18,18,0.95)', backdropFilter: 'blur(12px)' }}
    >
      {/* Hamburger — mobile only */}
      <button
        onClick={onMenuClick}
        className="p-2 rounded-lg text-gray-400 hover:text-white hover:bg-white/5 lg:hidden transition-colors"
      >
        <Menu className="h-5 w-5" />
      </button>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Alert bell */}
      <AlertBell unreadCount={unreadCount} />

      {/* User menu */}
      <div className="flex items-center gap-3">
        <span className="hidden sm:block text-sm text-gray-400 font-medium">
          {user?.first_name ?? user?.username}
        </span>
        <button
          onClick={handleLogout}
          title="Log out"
          className="p-2 rounded-lg text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
        >
          <LogOut className="h-4 w-4" />
        </button>
      </div>
    </header>
  )
}
