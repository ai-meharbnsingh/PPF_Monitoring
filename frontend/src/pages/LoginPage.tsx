import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '@/hooks/useAuth'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { AlertTriangle } from 'lucide-react'

interface LoginFormValues {
  username: string
  password: string
}

export default function LoginPage() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const redirect = searchParams.get('redirect') ?? '/admin/dashboard'
  const { login, isLoading, error, isAuthenticated, user } = useAuth()

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginFormValues>()

  // Already logged in?
  useEffect(() => {
    if (isAuthenticated && user) {
      if (user.is_temporary_password) {
        navigate('/change-password', { replace: true })
      } else {
        navigate(redirect, { replace: true })
      }
    }
  }, [isAuthenticated, user, navigate, redirect])

  const onSubmit = async (data: LoginFormValues) => {
    const result = await login(data)
    if (result.success) {
      // navigation handled by useEffect above
    }
  }

  return (
    <div className="min-h-screen bg-matte-black flex items-center justify-center p-4">
      {/* Subtle background glow */}
      <div
        className="fixed inset-0 pointer-events-none"
        style={{
          background: 'radial-gradient(ellipse 60% 50% at 50% 0%, rgba(0,240,255,0.06) 0%, transparent 70%)',
        }}
      />

      <div className="relative w-full max-w-sm">
        {/* Logo & title */}
        <div className="text-center mb-8">
          <div
            className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4"
            style={{
              background: 'rgba(0,240,255,0.12)',
              border: '1px solid rgba(0,240,255,0.4)',
              boxShadow: '0 0 30px rgba(0,240,255,0.15)',
            }}
          >
            <span className="text-electric-blue font-bold text-2xl">R</span>
          </div>
          <h1 className="text-2xl font-bold text-white tracking-wide">RG Auto Studio</h1>
          <p className="text-sm text-gray-500 mt-1">Sign in to your account</p>
        </div>

        {/* Form card */}
        <div
          className="rounded-2xl p-8"
          style={{
            background: 'rgba(18,18,18,0.9)',
            backdropFilter: 'blur(16px)',
            border: '1px solid rgba(255,255,255,0.08)',
          }}
        >
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <Input
              label="Username"
              placeholder="Enter your username"
              autoComplete="username"
              autoFocus
              {...register('username', { required: 'Username is required' })}
              error={errors.username?.message}
            />
            <Input
              label="Password"
              type="password"
              placeholder="Enter your password"
              autoComplete="current-password"
              {...register('password', { required: 'Password is required' })}
              error={errors.password?.message}
            />

            {/* API error */}
            {error && (
              <div className="flex items-start gap-2 p-3 rounded-lg border border-red-500/30 bg-red-500/10">
                <AlertTriangle className="h-4 w-4 text-red-400 shrink-0 mt-0.5" />
                <p className="text-sm text-red-400">{error}</p>
              </div>
            )}

            <Button type="submit" className="w-full" isLoading={isLoading}>
              Sign In
            </Button>
          </form>
        </div>

        <p className="text-center text-xs text-gray-600 mt-6 tracking-wide">
          RG Auto Studio Monitoring System
        </p>
      </div>
    </div>
  )
}
