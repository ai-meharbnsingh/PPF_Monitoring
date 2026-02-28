import { createBrowserRouter, RouterProvider, Navigate, Outlet } from 'react-router-dom'
import { AppLayout } from '@/components/layout/AppLayout'
import { ProtectedRoute } from '@/components/auth/ProtectedRoute'
import { Toaster } from 'react-hot-toast'

// ── Lazy-loaded pages ──────────────────────────────────────────────────────────
import { lazy, Suspense } from 'react'
import { PageSpinner } from '@/components/ui/Spinner'

const LoginPage = lazy(() => import('@/pages/LoginPage'))
const PublicSplashPage = lazy(() => import('@/pages/PublicSplashPage'))
const ChangePasswordPage = lazy(() => import('@/pages/ChangePasswordPage'))
const DashboardPage = lazy(() => import('@/pages/DashboardPage'))
const PitDetailPage = lazy(() => import('@/pages/PitDetailPage'))
const JobsPage = lazy(() => import('@/pages/JobsPage'))
const JobDetailPage = lazy(() => import('@/pages/JobDetailPage'))
const AlertsPage = lazy(() => import('@/pages/AlertsPage'))
const AlertConfigPage = lazy(() => import('@/pages/AlertConfigPage'))
const DevicesPage = lazy(() => import('@/pages/DevicesPage'))
const StaffPage = lazy(() => import('@/pages/StaffPage'))
const TrackingPage = lazy(() => import('@/pages/TrackingPage'))
const TrackByCodePage = lazy(() => import('@/pages/TrackByCodePage'))
const AdminPage = lazy(() => import('@/pages/AdminPage'))
const AdminPendingDevicesPage = lazy(() => import('@/pages/admin/AdminPendingDevicesPage'))
const AdminDeviceAssignmentsPage = lazy(() => import('@/pages/admin/AdminDeviceAssignmentsPage'))
const NotFoundPage = lazy(() => import('@/pages/NotFoundPage'))

function Lazy({ element }: { element: React.ReactNode }) {
  return <Suspense fallback={<PageSpinner />}>{element}</Suspense>
}

const router = createBrowserRouter([
  // ── Public routes ────────────────────────────────────────────────────────
  {
    path: '/',
    element: <Lazy element={<PublicSplashPage />} />,
  },
  {
    path: '/login',
    element: <Lazy element={<LoginPage />} />,
  },
  {
    path: '/track',
    element: <Lazy element={<TrackByCodePage />} />,
  },
  {
    path: '/track/:token',
    element: <Lazy element={<TrackingPage />} />,
  },

  // ── Auth: change password (before full access) ────────────────────────
  {
    path: '/change-password',
    element: (
      <ProtectedRoute>
        <Lazy element={<ChangePasswordPage />} />
      </ProtectedRoute>
    ),
  },

  // ── Main app (requires auth, renders AppLayout shell) ─────────────────
  {
    path: '/admin',
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <Navigate to="/admin/dashboard" replace /> },
      {
        path: 'dashboard',
        element: <Lazy element={<DashboardPage />} />,
      },
      {
        path: 'pits/:pitId',
        element: <Lazy element={<PitDetailPage />} />,
      },
      {
        path: 'jobs',
        element: <Lazy element={<JobsPage />} />,
      },
      {
        path: 'jobs/:jobId',
        element: <Lazy element={<JobDetailPage />} />,
      },
      {
        path: 'alerts',
        element: <Lazy element={<AlertsPage />} />,
      },

      // ── Owner/super_admin only ──────────────────────────────────────────
      {
        element: (
          <ProtectedRoute requiredRoles={['owner', 'super_admin']}>
            <Outlet />
          </ProtectedRoute>
        ),
        children: [
          {
            path: 'alerts/config',
            element: <Lazy element={<AlertConfigPage />} />,
          },
          {
            path: 'devices',
            element: <Lazy element={<DevicesPage />} />,
          },
          {
            path: 'staff',
            element: <Lazy element={<StaffPage />} />,
          },
          {
            path: 'metrics',
            element: <Lazy element={<AdminPage />} />,
          },
        ],
      },

      // ── Super admin only ──────────────────────────────────────────────────────
      {
        element: (
          <ProtectedRoute requiredRoles={['super_admin']}>
            <Outlet />
          </ProtectedRoute>
        ),
        children: [
          {
            path: 'devices/pending',
            element: <Lazy element={<AdminPendingDevicesPage />} />,
          },
          {
            path: 'devices/assignments',
            element: <Lazy element={<AdminDeviceAssignmentsPage />} />,
          },
        ],
      },
    ],
  },

  // ── Catch-all ────────────────────────────────────────────────────────────
  {
    path: '*',
    element: <Lazy element={<NotFoundPage />} />,
  },
])

export function App() {
  return (
    <>
      <RouterProvider router={router} />
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          style: {
            fontSize: '14px',
            borderRadius: '10px',
            border: '1px solid #e5e7eb',
          },
        }}
      />
    </>
  )
}
