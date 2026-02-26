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
import {
  Plus,
  Users,
  Key,
  Pencil,
  Shield,
  UserCheck,
  UserX,
} from 'lucide-react'
import { formatRelative } from '@/utils/formatters'
import { useForm } from 'react-hook-form'
import toast from 'react-hot-toast'

type RoleTab = 'all' | 'owner' | 'staff'

interface CreateFormValues {
  username: string
  password: string
  first_name: string
  last_name: string
  email: string
  phone: string
  role: 'staff' | 'owner'
}

interface EditFormValues {
  first_name: string
  last_name: string
  email: string
  phone: string
}

const ROLE_TABS: { key: RoleTab; label: string; icon: React.ReactNode }[] = [
  { key: 'all', label: 'All', icon: <Users className="h-3.5 w-3.5" /> },
  { key: 'owner', label: 'Owners', icon: <Shield className="h-3.5 w-3.5" /> },
  { key: 'staff', label: 'Staff', icon: <UserCheck className="h-3.5 w-3.5" /> },
]

export default function StaffPage() {
  const workshopId = useAppSelector((s) => s.auth.user?.workshop_id)
  const userRole = useAppSelector((s) => s.auth.user?.role)
  const isSuperAdmin = userRole === 'super_admin'
  const [users, setUsers] = useState<UserResponse[]>([])
  const [loading, setLoading] = useState(true)
  const [createOpen, setCreateOpen] = useState(false)
  const [editUser, setEditUser] = useState<UserResponse | null>(null)
  const [resetUserId, setResetUserId] = useState<number | null>(null)
  const [tempPassword, setTempPassword] = useState<string | null>(null)
  const [activeTab, setActiveTab] = useState<RoleTab>('all')

  const createForm = useForm<CreateFormValues>()
  const editForm = useForm<EditFormValues>()

  const loadUsers = useCallback(async () => {
    if (!workshopId) return
    setLoading(true)
    try {
      const resp = await usersApi.list(workshopId)
      setUsers(resp.items.filter((u) => u.role === 'staff' || u.role === 'owner'))
    } catch {
      toast.error('Failed to load team members')
    } finally {
      setLoading(false)
    }
  }, [workshopId])

  useEffect(() => {
    void loadUsers()
  }, [loadUsers])

  const filteredUsers =
    activeTab === 'all' ? users : users.filter((u) => u.role === activeTab)

  const onCreateSubmit = async (data: CreateFormValues) => {
    if (!workshopId) return
    try {
      await usersApi.create({
        username: data.username,
        password: data.password,
        role: data.role,
        first_name: data.first_name || undefined,
        last_name: data.last_name || undefined,
        email: data.email || undefined,
        phone: data.phone || undefined,
        workshop_id: workshopId,
      })
      toast.success(`${data.role === 'owner' ? 'Owner' : 'Staff member'} created!`)
      createForm.reset()
      setCreateOpen(false)
      void loadUsers()
    } catch {
      toast.error('Failed to create user')
    }
  }

  const onEditSubmit = async (data: EditFormValues) => {
    if (!editUser) return
    try {
      await usersApi.update(editUser.id, {
        first_name: data.first_name || undefined,
        last_name: data.last_name || undefined,
        email: data.email || undefined,
        phone: data.phone || undefined,
      })
      toast.success('User updated')
      setEditUser(null)
      void loadUsers()
    } catch {
      toast.error('Failed to update user')
    }
  }

  const handleDeactivate = async (user: UserResponse) => {
    const action = user.is_active ? 'deactivate' : 'reactivate'
    try {
      if (user.is_active) {
        await usersApi.deactivate(user.id)
      } else {
        await usersApi.update(user.id, { is_active: true })
      }
      toast.success(`User ${action}d`)
      void loadUsers()
    } catch {
      toast.error(`Failed to ${action} user`)
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

  const openEditModal = (user: UserResponse) => {
    editForm.reset({
      first_name: user.first_name ?? '',
      last_name: user.last_name ?? '',
      email: user.email ?? '',
      phone: user.phone ?? '',
    })
    setEditUser(user)
  }

  return (
    <div className="p-6 max-w-3xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div>
          <h1 className="text-xl font-bold text-white">Team Management</h1>
          <p className="text-xs text-gray-500 mt-0.5">
            {users.length} member{users.length !== 1 ? 's' : ''}
          </p>
        </div>
        <Button
          size="sm"
          leftIcon={<Plus className="h-4 w-4" />}
          onClick={() => setCreateOpen(true)}
        >
          Add Member
        </Button>
      </div>

      {/* Role filter tabs */}
      <div className="flex items-center gap-1 mb-4 p-1 bg-white/[0.04] rounded-lg w-fit">
        {ROLE_TABS.map((tab) => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`flex items-center gap-1.5 px-3 py-1.5 text-xs font-medium rounded-md transition-all ${activeTab === tab.key
              ? 'bg-electric-blue/15 text-electric-blue'
              : 'text-gray-500 hover:text-gray-300'
              }`}
          >
            {tab.icon}
            {tab.label}
          </button>
        ))}
      </div>

      {/* User list */}
      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => <Skeleton key={i} className="h-16" />)}
        </div>
      ) : filteredUsers.length === 0 ? (
        <EmptyState
          icon={<Users className="h-12 w-12" />}
          title={`No ${activeTab === 'all' ? '' : activeTab + ' '}members`}
          description="Add your first team member."
          action={
            <Button size="sm" onClick={() => setCreateOpen(true)}>Add Member</Button>
          }
        />
      ) : (
        <div className="space-y-2">
          {filteredUsers.map((user) => (
            <div
              key={user.id}
              className="card p-4 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
            >
              <div className="flex items-center gap-3 min-w-0">
                <div className={`h-9 w-9 rounded-full flex items-center justify-center shrink-0 ${user.role === 'owner'
                  ? 'bg-champagne-gold/15'
                  : 'bg-electric-blue/15'
                  }`}>
                  <span className={`font-semibold text-sm uppercase ${user.role === 'owner' ? 'text-champagne-gold' : 'text-electric-blue'
                    }`}>
                    {user.first_name?.[0] ?? user.username[0]}
                  </span>
                </div>
                <div className="min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <p className="font-medium text-white text-sm truncate">
                      {user.first_name
                        ? `${user.first_name} ${user.last_name ?? ''}`.trim()
                        : user.username}
                    </p>
                    <Badge variant={user.is_active ? 'success' : 'danger'} dot>
                      {user.is_active ? 'Active' : 'Inactive'}
                    </Badge>
                    <Badge variant={user.role === 'owner' ? 'warning' : 'default'}>
                      {user.role}
                    </Badge>
                  </div>
                  <p className="text-xs text-gray-500 truncate">
                    @{user.username}
                    {user.last_login && ` · Last login ${formatRelative(user.last_login)}`}
                  </p>
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 shrink-0">
                <Button
                  size="sm"
                  variant="secondary"
                  leftIcon={<Pencil className="h-3.5 w-3.5" />}
                  onClick={() => openEditModal(user)}
                >
                  Edit
                </Button>
                <Button
                  size="sm"
                  variant="secondary"
                  leftIcon={<Key className="h-3.5 w-3.5" />}
                  onClick={() => void handleResetPassword(user.id)}
                >
                  Reset
                </Button>
                <Button
                  size="sm"
                  variant={user.is_active ? 'danger' : 'primary'}
                  leftIcon={user.is_active
                    ? <UserX className="h-3.5 w-3.5" />
                    : <UserCheck className="h-3.5 w-3.5" />
                  }
                  onClick={() => void handleDeactivate(user)}
                >
                  {user.is_active ? 'Deactivate' : 'Activate'}
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Create modal */}
      <Modal isOpen={createOpen} onClose={() => setCreateOpen(false)} title="Add Team Member" size="md">
        <form onSubmit={createForm.handleSubmit(onCreateSubmit)} className="space-y-4">
          {/* Role selector for super_admin */}
          {isSuperAdmin && (
            <div className="flex items-center gap-3">
              <label className="text-sm text-gray-400">Role</label>
              <div className="flex gap-2">
                {(['staff', 'owner'] as const).map((r) => (
                  <label key={r} className="flex items-center gap-1.5 cursor-pointer">
                    <input
                      type="radio"
                      value={r}
                      defaultChecked={r === 'staff'}
                      {...createForm.register('role')}
                      className="accent-electric-blue"
                    />
                    <span className="text-sm text-gray-300 capitalize">{r}</span>
                  </label>
                ))}
              </div>
            </div>
          )}
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input
              label="Username *"
              {...createForm.register('username', { required: 'Required' })}
              error={createForm.formState.errors.username?.message}
            />
            <Input
              label="Password *"
              type="password"
              hint="8+ chars, 1 uppercase, 1 digit"
              {...createForm.register('password', {
                required: 'Required',
                minLength: { value: 8, message: 'Min 8 chars' },
                validate: {
                  hasUpper: (v) => /[A-Z]/.test(v) || 'Needs uppercase',
                  hasDigit: (v) => /\d/.test(v) || 'Needs digit',
                },
              })}
              error={createForm.formState.errors.password?.message}
            />
          </div>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="First Name" {...createForm.register('first_name')} />
            <Input label="Last Name" {...createForm.register('last_name')} />
          </div>
          <Input label="Email" type="email" {...createForm.register('email')} />
          <Input label="Phone" placeholder="+91..." {...createForm.register('phone')} />
          <div className="flex justify-end gap-3">
            <Button variant="secondary" type="button" onClick={() => setCreateOpen(false)}>Cancel</Button>
            <Button type="submit" isLoading={createForm.formState.isSubmitting}>Create</Button>
          </div>
        </form>
      </Modal>

      {/* Edit modal */}
      <Modal isOpen={!!editUser} onClose={() => setEditUser(null)} title="Edit Team Member" size="md">
        <form onSubmit={editForm.handleSubmit(onEditSubmit)} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <Input label="First Name" {...editForm.register('first_name')} />
            <Input label="Last Name" {...editForm.register('last_name')} />
          </div>
          <Input label="Email" type="email" {...editForm.register('email')} />
          <Input label="Phone" placeholder="+91..." {...editForm.register('phone')} />
          <div className="flex justify-end gap-3">
            <Button variant="secondary" type="button" onClick={() => setEditUser(null)}>Cancel</Button>
            <Button type="submit" isLoading={editForm.formState.isSubmitting}>Save Changes</Button>
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
          <p className="text-sm text-gray-400">Share this temporary password with the team member:</p>
          <div className="bg-white/[0.06] rounded-lg px-4 py-3 font-mono text-sm text-white text-center border border-white/10">
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
