import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { useNavigate } from 'react-router-dom'
import { authApi } from '@/api/auth'
import { Input } from '@/components/ui/Input'
import { Button } from '@/components/ui/Button'
import { useAuth } from '@/hooks/useAuth'
import { AlertTriangle, KeyRound } from 'lucide-react'
import toast from 'react-hot-toast'

interface FormValues {
  current_password: string
  new_password: string
  confirm_password: string
}

export default function ChangePasswordPage() {
  const navigate = useNavigate()
  const { user, markPasswordChanged } = useAuth()
  const [apiError, setApiError] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm<FormValues>()

  const newPw = watch('new_password')

  const onSubmit = async (data: FormValues) => {
    setApiError(null)
    try {
      await authApi.changePassword({
        current_password: data.current_password,
        new_password: data.new_password,
      })
      markPasswordChanged()
      toast.success('Password changed successfully!')
      navigate('/dashboard', { replace: true })
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
      setApiError(typeof detail === 'string' ? detail : 'Failed to change password.')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-slate-100 flex items-center justify-center p-4">
      <div className="w-full max-w-sm">
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-14 h-14 rounded-2xl bg-amber-500 shadow-lg mb-4">
            <KeyRound className="text-white h-6 w-6" />
          </div>
          <h1 className="text-2xl font-bold text-gray-900">Change Password</h1>
          {user?.is_temporary_password && (
            <p className="text-sm text-amber-600 mt-1 font-medium">
              You must change your temporary password before continuing.
            </p>
          )}
        </div>

        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8">
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-5">
            <Input
              label="Current Password"
              type="password"
              autoComplete="current-password"
              {...register('current_password', { required: 'Current password is required' })}
              error={errors.current_password?.message}
            />
            <Input
              label="New Password"
              type="password"
              autoComplete="new-password"
              hint="At least 8 chars, 1 uppercase, 1 digit"
              {...register('new_password', {
                required: 'New password is required',
                minLength: { value: 8, message: 'At least 8 characters required' },
                validate: {
                  hasUpper: (v) => /[A-Z]/.test(v) || 'Must contain an uppercase letter',
                  hasDigit: (v) => /\d/.test(v) || 'Must contain a digit',
                },
              })}
              error={errors.new_password?.message}
            />
            <Input
              label="Confirm New Password"
              type="password"
              autoComplete="new-password"
              {...register('confirm_password', {
                required: 'Please confirm your password',
                validate: (v) => v === newPw || 'Passwords do not match',
              })}
              error={errors.confirm_password?.message}
            />

            {apiError && (
              <div className="flex items-start gap-2 p-3 rounded-lg bg-red-50 border border-red-200">
                <AlertTriangle className="h-4 w-4 text-red-500 shrink-0 mt-0.5" />
                <p className="text-sm text-red-700">{apiError}</p>
              </div>
            )}

            <Button type="submit" className="w-full" isLoading={isSubmitting}>
              Change Password
            </Button>
          </form>
        </div>
      </div>
    </div>
  )
}
