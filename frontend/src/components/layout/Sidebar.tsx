import { NavLink } from 'react-router-dom'
import { clsx } from 'clsx'
import {
  LayoutDashboard,
  Briefcase,
  Bell,
  Cpu,
  Users,
  ShieldCheck,
  X,
} from 'lucide-react'
import { useAppSelector } from '@/hooks/useAppDispatch'
import type { UserRole } from '@/types/common'

interface NavItem {
  to: string
  label: string
  icon: React.ReactNode
  roles: UserRole[]
}

const NAV_ITEMS: NavItem[] = [
  {
    to: '/admin/dashboard',
    label: 'Dashboard',
    icon: <LayoutDashboard className="h-5 w-5" />,
    roles: ['super_admin', 'owner', 'staff'],
  },
  {
    to: '/admin/jobs',
    label: 'Jobs',
    icon: <Briefcase className="h-5 w-5" />,
    roles: ['super_admin', 'owner', 'staff'],
  },
  {
    to: '/admin/alerts',
    label: 'Alerts',
    icon: <Bell className="h-5 w-5" />,
    roles: ['super_admin', 'owner', 'staff'],
  },
  {
    to: '/admin/devices',
    label: 'Devices',
    icon: <Cpu className="h-5 w-5" />,
    roles: ['super_admin', 'owner'],
  },
  {
    to: '/admin/staff',
    label: 'Team',
    icon: <Users className="h-5 w-5" />,
    roles: ['super_admin', 'owner'],
  },
  {
    to: '/admin/metrics',
    label: 'Admin',
    icon: <ShieldCheck className="h-5 w-5" />,
    roles: ['super_admin'],
  },
]

interface SidebarProps {
  isOpen: boolean
  onClose: () => void
}

export function Sidebar({ isOpen, onClose }: SidebarProps) {
  const user = useAppSelector((s) => s.auth.user)

  const visibleItems = NAV_ITEMS.filter(
    (item) => user && item.roles.includes(user.role),
  )

  return (
    <>
      {/* Overlay on mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 z-20 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={clsx(
          'fixed top-0 left-0 z-30 h-screen w-64',
          'flex flex-col transition-transform duration-200 ease-in-out',
          'lg:translate-x-0 lg:static lg:z-auto',
          'border-r border-white/[0.08]',
          isOpen ? 'translate-x-0' : '-translate-x-full',
        )}
        style={{ background: 'rgba(18,18,18,0.97)', backdropFilter: 'blur(12px)' }}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-5 py-5 border-b border-white/[0.08]">
          <div className="flex items-center gap-3">
            <div
              className="h-9 w-9 rounded-full flex items-center justify-center"
              style={{
                background: 'rgba(0,240,255,0.15)',
                border: '1px solid rgba(0,240,255,0.4)',
              }}
            >
              <span className="text-electric-blue font-bold text-lg">R</span>
            </div>
            <span className="font-semibold text-white text-sm tracking-wide">RG Auto Studio</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-gray-500 hover:text-white hover:bg-white/5 lg:hidden transition-colors"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Workshop info */}
        {user?.workshop_name && (
          <div className="px-5 py-3 border-b border-white/[0.08]">
            <p className="text-xs font-medium text-gray-600 uppercase tracking-widest">Workshop</p>
            <p className="text-sm font-semibold text-gray-200 mt-0.5 truncate">
              {user.workshop_name}
            </p>
          </div>
        )}

        {/* Nav */}
        <nav className="flex-1 overflow-y-auto px-3 py-4 space-y-0.5">
          {visibleItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.to === '/admin/dashboard'}
              onClick={() => {
                if (window.innerWidth < 1024) onClose()
              }}
              className={({ isActive }) =>
                clsx('sidebar-link', isActive && 'active')
              }
            >
              {item.icon}
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="px-4 py-4 border-t border-white/[0.08]">
          <div className="flex items-center gap-3">
            <div
              className="h-8 w-8 rounded-full flex items-center justify-center shrink-0"
              style={{
                background: 'rgba(0,240,255,0.15)',
                border: '1px solid rgba(0,240,255,0.3)',
              }}
            >
              <span className="text-electric-blue font-semibold text-xs uppercase">
                {user?.first_name?.[0] ?? user?.username?.[0] ?? '?'}
              </span>
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-white truncate">
                {user?.first_name ?? user?.username}
              </p>
              <p className="text-xs text-gray-500 capitalize">{user?.role?.replace('_', ' ')}</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
