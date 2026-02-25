import { type ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { useAppSelector } from '@/hooks/useAppDispatch'
import type { UserRole } from '@/types/common'
import { PageSpinner } from '@/components/ui/Spinner'

interface ProtectedRouteProps {
  children: ReactNode
  requiredRoles?: UserRole[]
}

export function ProtectedRoute({ children, requiredRoles }: ProtectedRouteProps) {
  const location = useLocation()
  const { isAuthenticated, user, isLoading } = useAppSelector((s) => s.auth)

  if (isLoading) return <PageSpinner />

  // Not authenticated → redirect to home
  if (!isAuthenticated || !user) {
    return <Navigate to="/" replace />
  }

  // Force password change if temp password, except if already going there
  if (user.is_temporary_password && location.pathname !== '/change-password') {
    return <Navigate to="/change-password" replace />
  }

  // Role guard
  if (requiredRoles && !requiredRoles.includes(user.role)) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[400px] text-center p-8">
        <div className="text-4xl mb-4">🔒</div>
        <h2 className="text-xl font-semibold text-gray-800 mb-2">Access Denied</h2>
        <p className="text-sm text-gray-500">
          You don&apos;t have permission to view this page.
        </p>
      </div>
    )
  }

  return <>{children}</>
}

/** Inline role gate — renders children only if user has required role */
export function RoleGuard({
  roles,
  children,
}: {
  roles: UserRole[]
  children: ReactNode
}) {
  const user = useAppSelector((s) => s.auth.user)
  if (!user || !roles.includes(user.role)) return null
  return <>{children}</>
}
