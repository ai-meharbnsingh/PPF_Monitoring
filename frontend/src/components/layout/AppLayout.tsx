import { useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Sidebar } from './Sidebar'
import { Topbar } from './Topbar'
import { AlertPanel } from '@/components/alerts/AlertPanel'
import { useWebSocket } from '@/hooks/useWebSocket'
import { ErrorBoundary } from '@/components/ui/ErrorBoundary'

export function AppLayout() {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  // Connect WebSocket and wire all events to Redux
  useWebSocket()

  return (
    <div className="flex h-screen overflow-hidden bg-gray-50">
      <Sidebar isOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        <Topbar onMenuClick={() => setSidebarOpen(true)} />
        <main className="flex-1 overflow-y-auto">
          <ErrorBoundary>
            <Outlet />
          </ErrorBoundary>
        </main>
      </div>

      {/* Slide-in alert panel */}
      <AlertPanel />
    </div>
  )
}
