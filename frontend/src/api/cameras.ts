/**
 * Camera API Client
 * Handles all camera-related API calls
 */

import apiClient from './client'
import type { Camera, CameraAssignmentRequest } from '@/types/camera'

export interface CameraApiResponse {
  data: Camera | Camera[]
  message?: string
}

/**
 * Get discovered (unassigned) cameras for a workshop
 */
export async function getDiscoveredCameras(workshopId: number): Promise<Camera[]> {
  const response = await apiClient.get('/cameras/discovered', {
    params: { workshop_id: workshopId }
  })
  return response.data
}

/**
 * Get all cameras for a workshop
 */
export async function getWorkshopCameras(
  workshopId: number,
  includeAssigned = true
): Promise<Camera[]> {
  const response = await apiClient.get(`/cameras/workshop/${workshopId}`, {
    params: { include_assigned: includeAssigned }
  })
  return response.data
}

/**
 * Get a specific camera by ID
 */
export async function getCamera(cameraId: number): Promise<Camera> {
  const response = await apiClient.get(`/cameras/${cameraId}`)
  return response.data
}

/**
 * Get camera assigned to a pit
 */
export async function getCameraByPit(pitId: number): Promise<Camera | null> {
  const response = await apiClient.get(`/cameras/pit/${pitId}`)
  return response.data
}

/**
 * Trigger camera discovery scan
 */
export async function triggerCameraDiscovery(workshopId: number): Promise<{
  message: string
  available_cameras: number
  cameras: Camera[]
}> {
  const response = await apiClient.post('/cameras/discover', null, {
    params: { workshop_id: workshopId }
  })
  return response.data
}

/**
 * Assign camera to a pit
 */
export async function assignCameraToPit(
  cameraId: number,
  pitId: number,
  customName?: string
): Promise<Camera> {
  const response = await apiClient.post(`/cameras/${cameraId}/assign`, {
    pit_id: pitId,
    custom_name: customName
  })
  return response.data
}

/**
 * Unassign camera from its pit
 */
export async function unassignCamera(cameraId: number): Promise<Camera> {
  const response = await apiClient.post(`/cameras/${cameraId}/unassign`)
  return response.data
}

/**
 * Update camera details
 */
export async function updateCamera(
  cameraId: number,
  updates: Partial<Camera>
): Promise<Camera> {
  const response = await apiClient.patch(`/cameras/${cameraId}`, updates)
  return response.data
}

/**
 * Delete a camera
 */
export async function deleteCamera(cameraId: number): Promise<void> {
  await apiClient.delete(`/cameras/${cameraId}`)
}

/**
 * Register a new camera (manual registration)
 */
export async function registerCamera(cameraData: {
  device_id: string
  name: string
  workshop_id: number
  camera_type?: string
  ip_address: string
  stream_urls?: Record<string, any>
  [key: string]: any
}): Promise<Camera> {
  const response = await apiClient.post('/cameras/register', cameraData)
  return response.data
}
