import { useState } from 'react'
import { Outlet, Navigate } from 'react-router-dom'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/Card'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { workshopsApi, CreateWorkshopPayload } from '@/api/workshops'
import { Workshop } from '@/types/common'
import { toast } from 'react-hot-toast'

export default function AdminPage() {
    const queryClient = useQueryClient()
    const [formData, setFormData] = useState<CreateWorkshopPayload>({
        name: '',
        slug: '',
        contact_email: '',
        contact_phone: ''
    })

    // Fetch workshops
    const { data: workshops, isLoading } = useQuery({
        queryKey: ['admin_workshops'],
        queryFn: workshopsApi.getAll
    })

    // Create workshop mutation
    const createMutation = useMutation({
        mutationFn: workshopsApi.create,
        onSuccess: () => {
            toast.success('Workshop created successfully!')
            queryClient.invalidateQueries({ queryKey: ['admin_workshops'] })
            setFormData({ name: '', slug: '', contact_email: '', contact_phone: '' })
        },
        onError: (error: any) => {
            toast.error(error?.response?.data?.detail?.[0]?.msg || error?.response?.data?.detail || 'Failed to create workshop')
        }
    })

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault()
        if (!formData.name || !formData.slug) {
            toast.error('Name and Slug are required')
            return
        }
        createMutation.mutate(formData)
    }

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-6">
            <h1 className="text-2xl font-bold text-white mb-6">Super Admin Dashboard</h1>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Workshop List */}
                <Card className="bg-matte-black border-white/[0.08]">
                    <CardHeader>
                        <CardTitle className="text-lg text-white">Workshops</CardTitle>
                        <CardDescription>Manage all workshops across the platform.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {isLoading ? (
                            <p className="text-gray-400">Loading...</p>
                        ) : workshops?.length === 0 ? (
                            <p className="text-gray-500 italic">No workshops found.</p>
                        ) : (
                            <ul className="space-y-3">
                                {workshops?.map((ws: Workshop) => (
                                    <li key={ws.id} className="p-4 bg-white/[0.02] border border-white/[0.05] rounded-xl flex justify-between items-center">
                                        <div>
                                            <p className="font-semibold text-white">{ws.name}</p>
                                            <p className="text-xs text-electric-blue">{ws.slug}</p>
                                        </div>
                                        <div className="text-right text-sm text-gray-400">
                                            <p>ID: {ws.id}</p>
                                            <p>{ws.contact_phone || 'No phone'}</p>
                                        </div>
                                    </li>
                                ))}
                            </ul>
                        )}
                    </CardContent>
                </Card>

                {/* Create Workshop Form */}
                <Card className="bg-matte-black border-white/[0.08]">
                    <CardHeader>
                        <CardTitle className="text-lg text-white">Create New Workshop</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <form onSubmit={handleSubmit} className="space-y-4">
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Workshop Name *</label>
                                <input
                                    type="text"
                                    value={formData.name}
                                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-electric-blue focus:ring-1 focus:ring-electric-blue outline-none transition-all"
                                    placeholder="e.g. Delhi PPF Hub"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-medium text-gray-300 mb-1">Slug *</label>
                                <input
                                    type="text"
                                    value={formData.slug}
                                    onChange={(e) => setFormData({ ...formData, slug: e.target.value })}
                                    className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-white focus:border-electric-blue focus:ring-1 focus:ring-electric-blue outline-none transition-all"
                                    placeholder="e.g. delhi-ppf"
                                />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Email</label>
                                    <input
                                        type="email"
                                        value={formData.contact_email}
                                        onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
                                        className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-white outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-300 mb-1">Phone</label>
                                    <input
                                        type="text"
                                        value={formData.contact_phone}
                                        onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
                                        className="w-full bg-black/40 border border-white/10 rounded-lg px-4 py-2 text-white outline-none"
                                    />
                                </div>
                            </div>
                            <button
                                type="submit"
                                disabled={createMutation.isPending}
                                className="w-full bg-electric-blue text-black font-semibold py-2 rounded-lg hover:bg-electric-blue/90 disabled:opacity-50 transition-colors mt-2"
                            >
                                {createMutation.isPending ? 'Creating...' : 'Create Workshop'}
                            </button>
                        </form>
                    </CardContent>
                </Card>
            </div>
        </div>
    )
}
