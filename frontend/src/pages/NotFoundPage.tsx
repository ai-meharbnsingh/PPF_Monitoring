import { useNavigate } from 'react-router-dom'
import { Button } from '@/components/ui/Button'

export default function NotFoundPage() {
  const navigate = useNavigate()
  return (
    <div className="min-h-screen flex flex-col items-center justify-center text-center p-8">
      <p className="text-8xl font-bold text-gray-200">404</p>
      <h1 className="text-2xl font-semibold text-gray-800 mt-4">Page not found</h1>
      <p className="text-gray-500 mt-2 mb-8">The page you're looking for doesn't exist.</p>
      <Button onClick={() => navigate('/admin/dashboard')}>Go to Dashboard</Button>
    </div>
  )
}
