import { useEffect, useState, useCallback } from 'react'
import { usersApi } from '@/api/users'
import { useAppSelector } from '@/hooks/useAppDispatch'
import type { UserResponse } from '@/types/user'
import { Button } from '@/components/ui/Button'
import { Modal } from '@/components/ui/Modal'
import { Input } from '@/components/ui/Input'
import { Badge } from '@/components/ui/Badge'
import { Skeleton } from '@/components/ui/Spinner'
import { EmptyState } from '@/components/ui/EmptyState'
import { Plus, Users, Key } from 'lucide-react'
import { formatDate, formatRelative } from '@/utils/formatters'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'

interface CreateFormValues {
  username: string
  password: string
  first_name: string
  last_name: string
  email: string
  phone: string
}

export default function StaffPage() {
  const workshopId = useAppSelector((s) => s.auth.user?.workshop_id)
  const [users, setUsers] = useState<UserResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [resetUserId, setResetUserId] = useState<number | null>(null)
  const [tempPassword, setTempPassword] = useState<string | null>(null)

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors, isSubmitting },
  } = useForm<CreateFormValues>()

  const loadUsers = useCallback(async () => {
    if (!workshopId) return
    setLoading(true)
    try {
      const resp = await usersApi.list(workshopId)
      setUsers(resp.items.filter((u) => u.role === 'staff' || u.role === 'owner'))
    } catch {
      toast.error('Failed to load staff')
    } finally {
      setLoading(false)
    }
  }, [workshopId])

  useEffect(() => {
    void loadUsers()
  }, [loadUsers])

  const onCreateSubmit = async (data: CreateFormValues) => {
    if (!workshopId) return
    try {
      await usersApi.create({
        username: data.username,
        password: data.password,
        role: 'staff',
        first_name: data.first_name || undefined,
        last_name: data.last_name || undefined,
        email: data.email || undefined,
        phone: data.phone || undefined,
        workshop_id: workshopId,
      })
      toast.success('Staff member created!')
      reset()
      setCreateOpen(false)
      void loadUsers()
    } catch {
      toast.error('Failed to create staff member')
    }
  }

  const handleResetPassword = async (userId: number) => {
    try {
      const resp = await usersApi.resetPassword(userId, {})
      setTempPassword(resp.temporary_password ?? 'Password reset successfully')
      setResetUserId(userId)
    } catch {
      toast.error('Failed to reset password')
    }
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-bold text-gray-900">Staff</h1>
        <Button
          size="sm"
          leftIcon={<Plus className="h-4 w-4" />}
          onClick={() => setCreateOpen(true)}
        >
          Add Staff
        </Button>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-16" />)}
        </div>
      ) : users.length === 0 ? (
        <EmptyState
          icon={<Users className="h-12 w-12" />}
          title="No staff members"
          description="Add your first staff member."
          action={
            <Button size="sm" onClick={() => setCreateOpen(true)}>Add Staff</Button>
          }
        />
      ) : (
        <div className="space-y-2">
          {users.map((user) => (
            <div
              key={user.id}
              className="card p-4 flex items-center justify-between gap-4"
            >
              <div className="flex items-center gap-3">
                <div className="h-9 w-9 rounded-full bg-blue-100 flex items-center justify-center shrink-0">
                  <span className="text-blue-600 font-semibold text-sm uppercase">
                    {user.first_name?.[0] ?? user.username[0]}
                  </span>
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <p className="font-medium text-gray-900 text-sm">
                      {user.first_name
                        ? `${user.first_name} ${user.last_name ?? ''}`.trim()
                        : user.username}
                    </p>
                    <Badge variant={user.is_active ? 'success' : 'danger'} dot>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                    <Badge variant="default">
                      {user.role}
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-500">
                    @{user.username}
                    {user.last_login && ` · Last login ${formatRelative(user.last_login)}`}
                  </p>
                </div>
              </div>
              <Button
                size="sm"
                variant="secondary"
                leftIcon={<Key className="h-3.5 w-3.5" />}
                onClick={() => void handleResetPassword(user.id)}
              >
                Reset Password
              </Button>
            </div>
          ))}
        </div>
      )}

      {/* Create modal */}
      <Modal isOpen={createOpen} onClose={() => setCreateOpen(false)} title="Add Staff Member" size="md">
        <form onSubmit={handleSubmit(onCreateSubmit)} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <Input
              label="Username *"
              {...register('username', { required: 'Required' })}
              error={errors.username?.message}
            />
            <Input
              label="Password *"
              type="password"
              hint="8+ chars, 1 uppercase, 1 digit"
              {...register('password', {
                required: 'Required',
                minLength: { value: 8, message: 'Min 8 chars' },
                validate: {
                  hasUpper: (v) => /[A-Z]/.test(v) || 'Needs uppercase',
                  hasDigit: (v) => /\d/.test(v) || 'Needs digit',
                },
              })}
              error={errors.password?.message}
            />
          </div>
          <div className="grid grid-cols-2 gap-4">
            <Input label="First Name" {...register('first_name')} />
            <Input label="Last Name" {...register('last_name')} />
          </div>
          <Input label="Email" type="email" {...register('email')} />
          <Input label="Phone" placeholder="+91..." {...register('phone')} />
          <div className="flex justify-end gap-3">
            <Button variant="secondary" type="button" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit" isLoading={isSubmitting}>Create</Button>
          </div>
        </form>
      </Modal>

      {/* Reset password result */}
      <Modal
        isOpen={!!resetUserId && !!tempPassword}
        onClose={() => { setResetUserId(null); setTempPassword(null) }}
        title="Password Reset"
        size="sm"
      >
        <div className="space-y-3">
          <p className="text-sm text-gray-600">Share this temporary password with the staff member:</p>
          <div className="bg-gray-100 rounded-lg px-4 py-3 font-mono text-sm text-gray-900 text-center">
            {tempPassword}
          </div>
          <p className="text-xs text-gray-500">
            They will be asked to change it on next login.
          </p>
          <Button className="w-full" onClick={() => { setResetUserId(null); setTempPassword(null) }}>
            Done
          </Button>
        </div>
      </Modal>
    </div>
  )
}
