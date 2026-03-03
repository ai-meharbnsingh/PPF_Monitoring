/**
 * Camera Management Page
 * Allows users to view, discover, assign, and manage cameras
 */

import { useState, useEffect } from 'react'
import { useSelector } from 'react-redux'
import { RootState } from '@/store'
import { useWebSocket } from '@/hooks/useWebSocket'
import type { Camera, CameraNotification } from '@/types/camera'
import {
  getWorkshopCameras,
  getDiscoveredCameras,
  triggerCameraDiscovery,
  assignCameraToPit,
  unassignCamera,
  deleteCamera
} from '@/api/cameras'
import { getPits } from '@/api/pits'
import type { Pit } from '@/types/pit'
import { CameraStreamPlayer } from '@/components/video/CameraStreamPlayer'

export default function CamerasPage() {
  const { user } = useSelector((state: RootState) => state.auth)
  const workshopId = user?.workshop_id
  
  const [cameras, setCameras] = useState<Camera[]>([])
  const [discoveredCameras, setDiscoveredCameras] = useState<Camera[]>([])
  const [pits, setPits] = useState<Pit[]>([])
  const [loading, setLoading] = useState(true)
  const [discovering, setDiscovering] = useState(false)
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null)
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [showPreviewModal, setShowPreviewModal] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // WebSocket for real-time camera notifications
  const { lastMessage } = useWebSocket(workshopId)
  
  // Fetch cameras on mount
  useEffect(() => {
    if (workshopId) {
      fetchCameras()
      fetchPits()
    }
  }, [workshopId])
  
  // Handle WebSocket notifications
  useEffect(() => {
    if (lastMessage?.event === 'camera_notification') {
      const notification = lastMessage.data as CameraNotification
      handleCameraNotification(notification)
    }
  }, [lastMessage])
  
  const handleCameraNotification = (notification: CameraNotification) => {
    const { type, camera } = notification
    
    switch (type) {
      case 'camera_discovered':
        // Add to discovered list if not already there
        setDiscoveredCameras(prev => {
          const exists = prev.find(c => c.id === camera.id)
          if (exists) return prev
          return [...prev, camera]
        })
        break
      case 'camera_online':
      case 'camera_offline':
        // Update camera status
        setCameras(prev => prev.map(c => 
          c.id === camera.id ? { ...c, ...camera } : c
        ))
        setDiscoveredCameras(prev => prev.map(c => 
          c.id === camera.id ? { ...c, ...camera } : c
        ))
        break
    }
  }
  
  const fetchCameras = async () => {
    if (!workshopId) return
    
    try {
      setLoading(true)
      const [allCameras, discovered] = await Promise.all([
        getWorkshopCameras(workshopId),
        getDiscoveredCameras(workshopId)
      ])
      setCameras(allCameras)
      setDiscoveredCameras(discovered)
    } catch (err: any) {
      setError(err.message || 'Failed to fetch cameras')
    } finally {
      setLoading(false)
    }
  }
  
  const fetchPits = async () => {
    if (!workshopId) return
    
    try {
      const pitsData = await getPits(workshopId)
      setPits(pitsData)
    } catch (err) {
      console.error('Failed to fetch pits:', err)
    }
  }
  
  const handleDiscover = async () => {
    if (!workshopId) return
    
    try {
      setDiscovering(true)
      const result = await triggerCameraDiscovery(workshopId)
      setDiscoveredCameras(result.cameras)
      alert(`Discovery complete! Found ${result.available_cameras} cameras.`)
    } catch (err: any) {
      setError(err.message || 'Discovery failed')
    } finally {
      setDiscovering(false)
    }
  }
  
  const handleAssign = async (pitId: number) => {
    if (!selectedCamera) return
    
    try {
      await assignCameraToPit(selectedCamera.id, pitId)
      setShowAssignModal(false)
      setSelectedCamera(null)
      fetchCameras() // Refresh list
    } catch (err: any) {
      setError(err.message || 'Failed to assign camera')
    }
  }
  
  const handleUnassign = async (cameraId: number) => {
    if (!confirm('Are you sure you want to unassign this camera?')) return
    
    try {
      await unassignCamera(cameraId)
      fetchCameras() // Refresh list
    } catch (err: any) {
      setError(err.message || 'Failed to unassign camera')
    }
  }
  
  const handleDelete = async (cameraId: number) => {
    if (!confirm('Are you sure you want to delete this camera?')) return
    
    try {
      await deleteCamera(cameraId)
      fetchCameras() // Refresh list
    } catch (err: any) {
      setError(err.message || 'Failed to delete camera')
    }
  }
  
  const getStatusBadge = (camera: Camera) => {
    if (!camera.is_online) {
      return <span className="badge badge-error">Offline</span>
    }
    if (camera.is_assigned) {
      return <span className="badge badge-success">Assigned</span>
    }
    return <span className="badge badge-warning">Available</span>
  }
  
  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="loading loading-spinner loading-lg"></div>
      </div>
    )
  }
  
  return (
    <div className="container mx-auto p-6">
      {/* Header */}
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-3xl font-bold">📹 Camera Management</h1>
          <p className="text-gray-500 mt-1">
            Manage IP cameras and assign them to pits
          </p>
        </div>
        <button
          className={`btn btn-primary ${discovering ? 'loading' : ''}`}
          onClick={handleDiscover}
          disabled={discovering}
        >
          {discovering ? 'Scanning...' : '🔍 Discover Cameras'}
        </button>
      </div>
      
      {/* Error Alert */}
      {error && (
        <div className="alert alert-error mb-4">
          <span>{error}</span>
          <button className="btn btn-sm btn-ghost" onClick={() => setError(null)}>✕</button>
        </div>
      )}
      
      {/* Discovered Cameras Section */}
      {discoveredCameras.length > 0 && (
        <div className="mb-8">
          <h2 className="text-xl font-semibold mb-4">
            🆕 New Cameras ({discoveredCameras.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {discoveredCameras.map(camera => (
              <div key={camera.id} className="card bg-yellow-50 border border-yellow-200">
                <div className="card-body">
                  <h3 className="card-title text-lg">{camera.name}</h3>
                  <p className="text-sm text-gray-600">{camera.ip_address}</p>
                  <p className="text-xs text-gray-500">
                    Type: {camera.camera_type} | ID: {camera.device_id}
                  </p>
                  
                  <div className="card-actions justify-end mt-4">
                    <button
                      className="btn btn-sm btn-primary"
                      onClick={() => {
                        setSelectedCamera(camera)
                        setShowAssignModal(true)
                      }}
                    >
                      Assign to Pit
                    </button>
                    <button
                      className="btn btn-sm btn-ghost"
                      onClick={() => {
                        setSelectedCamera(camera)
                        setShowPreviewModal(true)
                      }}
                    >
                      Preview
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
      
      {/* All Cameras Section */}
      <div>
        <h2 className="text-xl font-semibold mb-4">
          📷 All Cameras ({cameras.length})
        </h2>
        
        {cameras.length === 0 ? (
          <div className="text-center py-12 bg-gray-50 rounded-lg">
            <p className="text-gray-500">No cameras found</p>
            <button
              className="btn btn-primary mt-4"
              onClick={handleDiscover}
            >
              Discover Cameras
            </button>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="table table-zebra w-full">
              <thead>
                <tr>
                  <th>Camera</th>
                  <th>IP Address</th>
                  <th>Status</th>
                  <th>Assigned To</th>
                  <th>Stream URL</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {cameras.map(camera => (
                  <tr key={camera.id}>
                    <td>
                      <div className="font-semibold">{camera.name}</div>
                      <div className="text-xs text-gray-500">{camera.device_id}</div>
                    </td>
                    <td>{camera.ip_address}</td>
                    <td>{getStatusBadge(camera)}</td>
                    <td>
                      {camera.pit_name ? (
                        <span className="badge badge-outline">{camera.pit_name}</span>
                      ) : (
                        <span className="text-gray-400">-</span>
                      )}
                    </td>
                    <td>
                      <div className="text-xs truncate max-w-xs">
                        {camera.primary_stream_url || '-'}
                      </div>
                    </td>
                    <td>
                      <div className="flex gap-2">
                        <button
                          className="btn btn-xs btn-ghost"
                          onClick={() => {
                            setSelectedCamera(camera)
                            setShowPreviewModal(true)
                          }}
                        >
                          Preview
                        </button>
                        {camera.is_assigned ? (
                          <button
                            className="btn btn-xs btn-warning"
                            onClick={() => handleUnassign(camera.id)}
                          >
                            Unassign
                          </button>
                        ) : (
                          <button
                            className="btn btn-xs btn-primary"
                            onClick={() => {
                              setSelectedCamera(camera)
                              setShowAssignModal(true)
                            }}
                          >
                            Assign
                          </button>
                        )}
                        <button
                          className="btn btn-xs btn-error btn-ghost"
                          onClick={() => handleDelete(camera.id)}
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
      
      {/* Assign Camera Modal */}
      {showAssignModal && selectedCamera && (
        <div className="modal modal-open">
          <div className="modal-box">
            <h3 className="font-bold text-lg mb-4">
              Assign Camera to Pit
            </h3>
            <p className="mb-4">
              Camera: <strong>{selectedCamera.name}</strong>
            </p>
            
            <div className="space-y-2 max-h-64 overflow-y-auto">
              {pits.map(pit => (
                <button
                  key={pit.id}
                  className="btn btn-outline w-full justify-start"
                  onClick={() => handleAssign(pit.id)}
                >
                  <span className="font-semibold">{pit.display_name || `Pit ${pit.pit_number}`}</span>
                  {pit.camera && (
                    <span className="text-xs text-warning ml-2">
                      (has camera)
                    </span>
                  )}
                </button>
              ))}
            </div>
            
            <div className="modal-action">
              <button
                className="btn btn-ghost"
                onClick={() => {
                  setShowAssignModal(false)
                  setSelectedCamera(null)
                }}
              >
                Cancel
              </button>
            </div>
          </div>
          <div className="modal-backdrop" onClick={() => setShowAssignModal(false)}></div>
        </div>
      )}
      
      {/* Preview Modal */}
      {showPreviewModal && selectedCamera && (
        <div className="modal modal-open">
          <div className="modal-box max-w-4xl">
            <h3 className="font-bold text-lg mb-4">
              Camera Preview: {selectedCamera.name}
            </h3>
            
            <div className="bg-black rounded-lg overflow-hidden aspect-video">
              {selectedCamera.primary_stream_url ? (
                <CameraStreamPlayer
                  streamUrl={selectedCamera.primary_stream_url}
                  className="w-full h-full"
                />
              ) : (
                <div className="flex items-center justify-center h-full text-gray-400">
                  No stream URL available
                </div>
              )}
            </div>
            
            <div className="mt-4 space-y-2 text-sm">
              <p><strong>Device ID:</strong> {selectedCamera.device_id}</p>
              <p><strong>IP Address:</strong> {selectedCamera.ip_address}</p>
              <p><strong>Status:</strong> {selectedCamera.is_online ? 'Online' : 'Offline'}</p>
              <p><strong>Stream URLs:</strong></p>
              <ul className="list-disc list-inside pl-4 space-y-1">
                {selectedCamera.stream_urls?.webrtc?.main && (
                  <li>WebRTC: {selectedCamera.stream_urls.webrtc.main}</li>
                )}
                {selectedCamera.stream_urls?.hls?.main && (
                  <li>HLS: {selectedCamera.stream_urls.hls.main}</li>
                )}
                {selectedCamera.stream_urls?.rtsp?.main && (
                  <li>RTSP: {selectedCamera.stream_urls.rtsp.main}</li>
                )}
              </ul>
            </div>
            
            <div className="modal-action">
              <button
                className="btn btn-primary"
                onClick={() => {
                  setShowPreviewModal(false)
                  setSelectedCamera(null)
                }}
              >
                Close
              </button>
            </div>
          </div>
          <div className="modal-backdrop" onClick={() => setShowPreviewModal(false)}></div>
        </div>
      )}
    </div>
  )
}
