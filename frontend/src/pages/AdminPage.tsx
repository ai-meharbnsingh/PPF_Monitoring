import { useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workshopsApi, CreateWorkshopPayload } from '@/api/workshops'
import { pitsApi, CreatePitPayload } from '@/api/pits'
import { usersApi } from '@/api/users'
import { Workshop } from '@/types/common'
import { toast } from 'react-hot-toast'
import { UserPlus, Building2 } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'

// Extend CreateWorkshopPayload for the form
interface WorkshopFormData extends CreateWorkshopPayload {
    owner_user_id?: number
}

export default function AdminPage() {
    const queryClient = useQueryClient()
    const [activeTab, setActiveTab] = useState<'workshop' | 'owner' | 'pit'>('workshop')
    
    // Workshop form
    const [formData, setFormData] = useState<WorkshopFormData>({
        name: '',
        email: '',
        phone: '',
        address: '',
        city: '',
        state: '',
        timezone: 'Asia/Kolkata',
        owner_user_id: undefined
    })
    
    // Owner user form
    const [ownerForm, setOwnerForm] = useState({
        username: '',
        email: '',
        first_name: '',
        last_name: '',
        password: '',
        workshop_id: undefined as number | undefined
    })
    
    // Pit form
    const [pitForm, setPitForm] = useState<CreatePitPayload & { workshop_id: string }>({
        workshop_id: '',
        pit_number: 1,
        name: '',
        description: '',
        camera_ip: '',
        camera_rtsp_url: '',
    })

    // Fetch workshops
    const { data: workshops, isLoading } = useQuery({
        queryKey: ['admin_workshops'],
        queryFn: workshopsApi.getAll
    })

    // Assign owner modal state
    const [assignOwnerModal, setAssignOwnerModal] = useState<{ open: boolean; workshop: Workshop | null }>({
        open: false,
        workshop: null
    })
    const [selectedOwnerId, setSelectedOwnerId] = useState<number | ''>('')

    // Assign owner mutation
    const assignOwnerMutation = useMutation({
        mutationFn: ({ workshopId, ownerId }: { workshopId: number; ownerId: number }) =>
            workshopsApi.assignOwner(workshopId, ownerId),
        onSuccess: () => {
            toast.success('Owner assigned successfully!')
            queryClient.invalidateQueries({ queryKey: ['admin_workshops'] })
            setAssignOwnerModal({ open: false, workshop: null })
            setSelectedOwnerId('')
        },
        onError: () => {
            toast.error('Failed to assign owner')
        }
    })

    // Fetch all users (for owner selection)
    const { data: users } = useQuery({
        queryKey: ['admin_users'],
        queryFn: async () => {
            const resp = await usersApi.listAll()
            return resp.items
        },
        enabled: activeTab === 'workshop'
    })

    // Create workshop mutation
    const createMutation = useMutation({
        mutationFn: (payload: WorkshopFormData) => {
            // Remove undefined values
            const cleanPayload: CreateWorkshopPayload = {
                name: payload.name,
                email: payload.email,
                phone: payload.phone,
                address: payload.address,
                city: payload.city,
                state: payload.state,
                timezone: payload.timezone,
            }
            if (payload.owner_user_id) {
                (cleanPayload as any).owner_user_id = payload.owner_user_id
            }
            return workshopsApi.create(cleanPayload)
        },
        onSuccess: () => {
            toast.success('Workshop created successfully!')
            queryClient.invalidateQueries({ queryKey: ['admin_workshops'] })
            setFormData({ 
                name: '', 
                email: '', 
                phone: '', 
                address: '', 
                city: '', 
                state: '', 
                timezone: 'Asia/Kolkata',
                owner_user_id: undefined 
            })
        },
        onError: (error: any) => {
            toast.error(error?.response?.data?.detail?.[0]?.msg || error?.response?.data?.detail || 'Failed to create workshop')
        }
    })

    // Create owner user mutation
    const createOwnerMutation = useMutation({
        mutationFn: async (data: typeof ownerForm) => {
            return usersApi.create({
                username: data.username,
                email: data.email,
                first_name: data.first_name,
                last_name: data.last_name,
                password: data.password,
                role: 'owner',
                workshop_id: data.workshop_id
            })
        },
        onSuccess: () => {
            toast.success('Owner user created successfully!')
            queryClient.invalidateQueries({ queryKey: ['admin_users'] })
            setOwnerForm({
                username: '',
                email: '',
                first_name: '',
                last_name: '',
                password: '',
                workshop_id: undefined
            })
        },
        onError: (error: any) => {
            toast.error(error?.response?.data?.detail?.[0]?.msg || error?.response?.data?.detail || 'Failed to create owner')
        }
    })

    // Create pit mutation
    const createPitMutation = useMutation({
        mutationFn: ({ workshopId, payload }: { workshopId: number; payload: CreatePitPayload }) =>
            pitsApi.createPit(workshopId, payload),
        onSuccess: () => {
            toast.success('Pit created successfully!')
            setPitForm({ workshop_id: '', pit_number: 1, name: '', description: '', camera_ip: '', camera_rtsp_url: '' })
        },
        onError: (error: any) => {
            toast.error(error?.response?.data?.detail?.[0]?.msg || error?.response?.data?.detail || 'Failed to create pit')
        }
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (!formData.name) {
            toast.error('Workshop Name is required')
            return
        }
        createMutation.mutate(formData)
    }

    const handleOwnerSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (!ownerForm.username || !ownerForm.password || !ownerForm.email) {
            toast.error('Username, email and password are required')
            return
        }
        createOwnerMutation.mutate(ownerForm)
    }

    const handlePitSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        const wsId = parseInt(pitForm.workshop_id)
        if (!wsId || !pitForm.pit_number) {
            toast.error('Workshop ID and Pit Number are required')
            return
        }
        const { workshop_id, ...payload } = pitForm
        createPitMutation.mutate({ workshopId: wsId, payload })
    }

    const ownerUsers = users?.filter((u: any) => u.role === 'owner') || []

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold text-white mb-6">Super Admin Dashboard</h1>

            {/* Tabs */}
            <div className="flex gap-2 mb-6">
                <Button
                    variant={activeTab === 'workshop' ? 'primary' : 'secondary'}
                    onClick={() => setActiveTab('workshop')}
                    leftIcon={<Building2 className="h-4 w-4" />}
                >
                    Create Workshop
                </Button>
                <Button
                    variant={activeTab === 'owner' ? 'primary' : 'secondary'}
                    onClick={() => setActiveTab('owner')}
                    leftIcon={<UserPlus className="h-4 w-4" />}
                >
                    Create Owner
                </Button>
                <Button
                    variant={activeTab === 'pit' ? 'primary' : 'secondary'}
                    onClick={() => setActiveTab('pit')}
                >
                    Create Pit
                </Button>
            </div>

            {/* Workshop Form */}
            {activeTab === 'workshop' && (
                <Card className="bg-matte-black border-white/[0.08]">
                    <CardHeader>
                        <CardTitle className="text-lg text-white">Create New Workshop</CardTitle>
                        <CardDescription>Create a workshop and optionally assign an owner.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Workshop Name *</label>
                                    <Input
                                        value={formData.name}
                                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                        placeholder="e.g. Delhi PPF Hub"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Owner User</label>
                                    <Select
                                        value={formData.owner_user_id?.toString() || ''}
                                        onChange={(e) => setFormData({ ...formData, owner_user_id: e.target.value ? parseInt(e.target.value) : undefined })}
                                        options={[
                                            { value: '', label: 'Select owner (optional)' },
                                            ...ownerUsers.map((u: any) => ({ 
                                                value: String(u.id), 
                                                label: `${u.username} (${u.email})` 
                                            })),
                                        ]}
                                    />
                                </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
                                    <Input
                                        type="email"
                                        value={formData.email || ''}
                                        onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                                        placeholder="workshop@example.com"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Phone</label>
                                    <Input
                                        value={formData.phone || ''}
                                        onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                                        placeholder="+91 98765 43210"
                                    />
                                </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">City</label>
                                    <Input
                                        value={formData.city || ''}
                                        onChange={(e) => setFormData({ ...formData, city: e.target.value })}
                                        placeholder="e.g. Delhi"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">State</label>
                                    <Input
                                        value={formData.state || ''}
                                        onChange={(e) => setFormData({ ...formData, state: e.target.value })}
                                        placeholder="e.g. Delhi"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Timezone</label>
                                    <Select
                                        value={formData.timezone}
                                        onChange={(e) => setFormData({ ...formData, timezone: e.target.value })}
                                        options={[
                                            { value: 'Asia/Kolkata', label: 'Asia/Kolkata (IST)' },
                                            { value: 'Asia/Dubai', label: 'Asia/Dubai' },
                                            { value: 'UTC', label: 'UTC' },
                                        ]}
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Address</label>
                                <Input
                                    value={formData.address || ''}
                                    onChange={(e) => setFormData({ ...formData, address: e.target.value })}
                                    placeholder="Full address"
                                />
                            </div>
                            <Button
                                type="submit"
                                isLoading={createMutation.isPending}
                                className="w-full"
                            >
                                Create Workshop
                            </Button>
                        </form>
                    </CardContent>
                </Card>
            )}

            {/* Owner Form */}
            {activeTab === 'owner' && (
                <Card className="bg-matte-black border-white/[0.08]">
                    <CardHeader>
                        <CardTitle className="text-lg text-white">Create Owner User</CardTitle>
                        <CardDescription>Create an owner user who can manage their workshop.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleOwnerSubmit} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Username *</label>
                                    <Input
                                        value={ownerForm.username}
                                        onChange={(e) => setOwnerForm({ ...ownerForm, username: e.target.value })}
                                        placeholder="e.g. owner_rajesh"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Email *</label>
                                    <Input
                                        type="email"
                                        value={ownerForm.email}
                                        onChange={(e) => setOwnerForm({ ...ownerForm, email: e.target.value })}
                                        placeholder="owner@example.com"
                                    />
                                </div>
                            </div>
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">First Name</label>
                                    <Input
                                        value={ownerForm.first_name}
                                        onChange={(e) => setOwnerForm({ ...ownerForm, first_name: e.target.value })}
                                        placeholder="Rajesh"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Last Name</label>
                                    <Input
                                        value={ownerForm.last_name}
                                        onChange={(e) => setOwnerForm({ ...ownerForm, last_name: e.target.value })}
                                        placeholder="Kumar"
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Password *</label>
                                <Input
                                    type="password"
                                    value={ownerForm.password}
                                    onChange={(e) => setOwnerForm({ ...ownerForm, password: e.target.value })}
                                    placeholder="Min 8 characters"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Assign to Workshop (Optional)</label>
                                <Select
                                    value={ownerForm.workshop_id?.toString() || ''}
                                    onChange={(e) => setOwnerForm({ ...ownerForm, workshop_id: e.target.value ? parseInt(e.target.value) : undefined })}
                                    options={[
                                        { value: '', label: 'No workshop (assign later)' },
                                        ...(workshops?.map((ws: Workshop) => ({ 
                                            value: String(ws.id), 
                                            label: `${ws.name} (ID: ${ws.id})` 
                                        })) || []),
                                    ]}
                                />
                            </div>
                            <Button
                                type="submit"
                                isLoading={createOwnerMutation.isPending}
                                className="w-full"
                            >
                                Create Owner
                            </Button>
                        </form>
                    </CardContent>
                </Card>
            )}

            {/* Pit Form */}
            {activeTab === 'pit' && (
                <Card className="bg-matte-black border-white/[0.08]">
                    <CardHeader>
                        <CardTitle className="text-lg text-white">Create New Pit</CardTitle>
                        <CardDescription>Add a pit/bay to an existing workshop.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handlePitSubmit} className="space-y-4">
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Workshop *</label>
                                    <Select
                                        value={pitForm.workshop_id}
                                        onChange={(e) => setPitForm({ ...pitForm, workshop_id: e.target.value })}
                                        options={[
                                            { value: '', label: 'Select workshop' },
                                            ...(workshops?.map((ws: Workshop) => ({ 
                                                value: String(ws.id), 
                                                label: `${ws.name} (ID: ${ws.id})` 
                                            })) || []),
                                        ]}
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Pit Number *</label>
                                    <Input
                                        type="number"
                                        min={1}
                                        max={50}
                                        value={pitForm.pit_number}
                                        onChange={(e) => setPitForm({ ...pitForm, pit_number: parseInt(e.target.value) || 1 })}
                                    />
                                </div>
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Pit Name</label>
                                <Input
                                    value={pitForm.name}
                                    onChange={(e) => setPitForm({ ...pitForm, name: e.target.value })}
                                    placeholder="e.g. Bay 1 - Premium"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Description</label>
                                <Input
                                    value={pitForm.description || ''}
                                    onChange={(e) => setPitForm({ ...pitForm, description: e.target.value })}
                                    placeholder="Optional description"
                                />
                            </div>
                            <Button
                                type="submit"
                                isLoading={createPitMutation.isPending}
                                className="w-full"
                            >
                                Create Pit
                            </Button>
                        </form>
                    </CardContent>
                </Card>
            )}

            {/* Workshop List */}
            <Card className="bg-matte-black border-white/[0.08]">
                <CardHeader>
                    <CardTitle className="text-lg text-white">All Workshops</CardTitle>
                </CardHeader>
                <CardContent>
                    {isLoading ? (
                        <p className="text-gray-400">Loading...</p>
                    ) : workshops?.length === 0 ? (
                        <p className="text-gray-500 italic">No workshops found.</p>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full">
                                <thead className="bg-white/5">
                                    <tr>
                                        <th className="text-left p-3 text-sm font-medium text-gray-400">ID</th>
                                        <th className="text-left p-3 text-sm font-medium text-gray-400">Name</th>
                                        <th className="text-left p-3 text-sm font-medium text-gray-400">Email</th>
                                        <th className="text-left p-3 text-sm font-medium text-gray-400">Owner</th>
                                        <th className="text-left p-3 text-sm font-medium text-gray-400">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {workshops?.map((ws: Workshop) => {
                                        // Find owner name from users list
                                        const owner = users?.find((u: any) => u.id === ws.owner_user_id)
                                        const ownerName = owner 
                                            ? `${owner.first_name || ''} ${owner.last_name || ''}`.trim() || owner.username
                                            : (ws.owner_user_id ? `User #${ws.owner_user_id}` : 'Unassigned')
                                        return (
                                            <tr key={ws.id}>
                                                <td className="p-3 text-white">{ws.id}</td>
                                                <td className="p-3 text-white">{ws.name}</td>
                                                <td className="p-3 text-gray-400">{ws.contact_email || '-'}</td>
                                                <td className="p-3 text-gray-400">{ownerName}</td>
                                                <td className="p-3">
                                                    <Button
                                                        size="sm"
                                                        variant="secondary"
                                                        onClick={() => {
                                                            setAssignOwnerModal({ open: true, workshop: ws })
                                                            setSelectedOwnerId(ws.owner_user_id || '')
                                                        }}
                                                    >
                                                        {ws.owner_user_id ? 'Change Owner' : 'Assign Owner'}
                                                    </Button>
                                                </td>
                                            </tr>
                                        )
                                    })}
                                </tbody>
                            </table>
                        </div>
                    )}
                </CardContent>
            </Card>

            {/* Assign Owner Modal */}
            {assignOwnerModal.open && assignOwnerModal.workshop && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
                    <div className="bg-[#1a1a1a] border border-white/10 rounded-xl p-6 w-full max-w-md">
                        <h3 className="text-lg font-bold text-white mb-4">
                            Assign Owner to {assignOwnerModal.workshop.name}
                        </h3>
                        <p className="text-sm text-gray-400 mb-4">
                            Select an owner user for this workshop
                        </p>
                        <select
                            value={selectedOwnerId}
                            onChange={(e) => setSelectedOwnerId(e.target.value ? parseInt(e.target.value) : '')}
                            className="w-full bg-[#1a1a1a] border-2 border-gray-600 rounded-lg px-3 py-2.5 text-white text-sm mb-4 focus:outline-none focus:border-cyan-400"
                        >
                            <option value="">-- Select Owner --</option>
                            {users?.filter((u: any) => u.role === 'owner' || u.role === 'super_admin').map((user: any) => (
                                <option key={user.id} value={user.id}>
                                    {user.first_name || user.last_name 
                                        ? `${user.first_name || ''} ${user.last_name || ''}`.trim() 
                                        : user.username} ({user.role})
                                </option>
                            ))}
                        </select>
                        <div className="flex justify-end gap-3">
                            <Button
                                variant="secondary"
                                onClick={() => {
                                    setAssignOwnerModal({ open: false, workshop: null })
                                    setSelectedOwnerId('')
                                }}
                            >
                                Cancel
                            </Button>
                            <Button
                                onClick={() => {
                                    if (selectedOwnerId && assignOwnerModal.workshop) {
                                        assignOwnerMutation.mutate({
                                            workshopId: assignOwnerModal.workshop.id,
                                            ownerId: Number(selectedOwnerId)
                                        })
                                    }
                                }}
                                isLoading={assignOwnerMutation.isPending}
                                disabled={!selectedOwnerId}
                            >
                                Assign Owner
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    )
}
