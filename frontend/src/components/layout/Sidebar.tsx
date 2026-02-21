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
    to: '/',
    label: 'Dashboard',
    icon: <LayoutDashboard className="h-5 w-5" />,
    roles: ['super_admin', 'owner', 'staff'],
  },
  {
    to: '/jobs',
    label: 'Jobs',
    icon: <Briefcase className="h-5 w-5" />,
    roles: ['super_admin', 'owner', 'staff'],
  },
  {
    to: '/alerts',
    label: 'Alerts',
    icon: <Bell className="h-5 w-5" />,
    roles: ['super_admin', 'owner', 'staff'],
  },
  {
    to: '/devices',
    label: 'Devices',
    icon: <Cpu className="h-5 w-5" />,
    roles: ['super_admin', 'owner'],
  },
  {
    to: '/staff',
    label: 'Staff',
    icon: <Users className="h-5 w-5" />,
    roles: ['super_admin', 'owner'],
  },
  {
    to: '/admin',
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
          className="fixed inset-0 z-20 bg-black/40 lg:hidden"
          onClick={onClose}
        />
      )}

      <aside
        className={clsx(
          'fixed top-0 left-0 z-30 h-screen w-64 bg-white border-r border-gray-200',
          'flex flex-col transition-transform duration-200 ease-in-out',
          'lg:translate-x-0 lg:static lg:z-auto',
          isOpen ? 'translate-x-0' : '-translate-x-full',
        )}
      >
        {/* Logo */}
        <div className="flex items-center justify-between px-5 py-5 border-b border-gray-100">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-lg bg-blue-600 flex items-center justify-center">
              <span className="text-white font-bold text-xs">PPF</span>
            </div>
            <span className="font-semibold text-gray-900 text-sm">PPF Monitor</span>
          </div>
          <button
            onClick={onClose}
            className="p-1 rounded-lg text-gray-400 hover:text-gray-600 hover:bg-gray-100 lg:hidden"
          >
            <X className="h-4 w-4" />
          </button>
        </div>

        {/* Workshop info */}
        {user?.workshop_name && (
          <div className="px-5 py-3 border-b border-gray-100">
            <p className="text-xs font-medium text-gray-400 uppercase tracking-wide">Workshop</p>
            <p className="text-sm font-semibold text-gray-700 mt-0.5 truncate">
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
              end={item.to === '/'}
              onClick={() => {
                if (window.innerWidth < 1024) onClose()
              }}
              className={({ isActive }) =>
                clsx(
                  'sidebar-link',
                  isActive && 'active',
                )
              }
            >
              {item.icon}
              <span>{item.label}</span>
            </NavLink>
          ))}
        </nav>

        {/* User footer */}
        <div className="px-4 py-4 border-t border-gray-100">
          <div className="flex items-center gap-2">
            <div className="h-8 w-8 rounded-full bg-blue-100 flex items-center justify-center">
              <span className="text-blue-600 font-semibold text-xs uppercase">
                {user?.first_name?.[0] ?? user?.username?.[0] ?? '?'}
              </span>
            </div>
            <div className="min-w-0">
              <p className="text-sm font-medium text-gray-800 truncate">
                {user?.first_name ?? user?.username}
              </p>
              <p className="text-xs text-gray-400 capitalize">{user?.role?.replace('_', ' ')}</p>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}
