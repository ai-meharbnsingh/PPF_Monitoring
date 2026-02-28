import { client } from './client'
import type { Workshop } from '@/types/common'

export interface CreateWorkshopPayload {
    name: string
    slug?: string
    email?: string
    phone?: string
    address?: string
    city?: string
    state?: string
    timezone?: string
    owner_user_id?: number
}

export const workshopsApi = {
    getAll: async () => {
        const response = await client.get('/workshops')
        console.log('Workshops API response:', response.data)
        const payload = response.data as any

        // Handle various response shapes robustly
        if (payload?.data?.items) return payload.data.items
        if (payload?.items) return payload.items
        if (Array.isArray(payload)) return payload

        return []
    },

    create: async (payload: CreateWorkshopPayload) => {
        const { data } = await client.post<{ data: Workshop }>('/workshops', payload)
        return data.data
    }
}
