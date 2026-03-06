/**
 * Camera Management Page
 * Allows users to view, discover, assign, and manage cameras
 */

import { useState, useEffect } from 'react'
import { useSelector } from 'react-redux'
import { RootState } from '@/store'
import type { Camera } from '@/types/camera'
import type { PitSummary } from '@/types/pit'
import {
  getWorkshopCameras,
  getDiscoveredCameras,
  triggerCameraDiscovery,
  assignCameraToPit,
  unassignCamera,
  deleteCamera,
} from '@/api/cameras'
import { pitsApi } from '@/api/pits'
import { CameraStreamPlayer } from '@/components/video/CameraStreamPlayer'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Modal } from '@/components/ui/Modal'
import { PageSpinner } from '@/components/ui/Spinner'
import toast from 'react-hot-toast'
import {
  Video,
  Search,
  RefreshCw,
  MapPin,
  Unlink,
  Trash2,
  Eye,
  Wifi,
  WifiOff,
} from 'lucide-react'

export default function CamerasPage() {
  const { user } = useSelector((state: RootState) => state.auth)
  
  // For super admin without workshop_id, default to 1
  const initialWorkshopId = user?.workshop_id || (user?.role === 'super_admin' ? 1 : null)
  const [workshopId] = useState<number | null>(initialWorkshopId)

  const [cameras, setCameras] = useState<Camera[]>([])
  const [discoveredCameras, setDiscoveredCameras] = useState<Camera[]>([])
  const [pits, setPits] = useState<PitSummary[]>([])
  const [loading, setLoading] = useState(true)
  const [discovering, setDiscovering] = useState(false)
  const [selectedCamera, setSelectedCamera] = useState<Camera | null>(null)
  const [showAssignModal, setShowAssignModal] = useState(false)
  const [showPreviewModal, setShowPreviewModal] = useState(false)
  
  console.log('CamerasPage render - user:', user?.role, 'workshopId:', workshopId)

  useEffect(() => {
    if (workshopId) {
      fetchCameras()
      fetchPits()
    }
  }, [workshopId])

  const fetchCameras = async () => {
    if (!workshopId) {
      console.log('No workshopId, skipping fetch')
      return
    }
    try {
      setLoading(true)
      console.log('Fetching cameras for workshop:', workshopId)
      const [allCameras, discovered] = await Promise.all([
        getWorkshopCameras(workshopId),
        getDiscoveredCameras(workshopId),
      ])
      console.log('Cameras fetched:', allCameras.length, 'Discovered:', discovered.length)
      setCameras(allCameras)
      setDiscoveredCameras(discovered)
    } catch (err: any) {
      console.error('Failed to fetch cameras:', err)
      toast.error('Failed to fetch cameras: ' + (err.message || 'Unknown error'))
    } finally {
      setLoading(false)
    }
  }

  const fetchPits = async () => {
    if (!workshopId) return
    try {
      const pitsData = await pitsApi.listPits(workshopId)
      setPits(pitsData)
    } catch {
      // Silently fail — pits list is supplementary
    }
  }

  const handleDiscover = async () => {
    if (!workshopId) return
    try {
      setDiscovering(true)
      const result = await triggerCameraDiscovery(workshopId)
      setDiscoveredCameras(result.cameras)
      toast.success(result.message)
    } catch {
      toast.error('Discovery failed')
    } finally {
      setDiscovering(false)
    }
  }

  const handleAssign = async (pitId: number) => {
    if (!selectedCamera) return
    try {
      await assignCameraToPit(selectedCamera.id, pitId)
      toast.success('Camera assigned successfully')
      setShowAssignModal(false)
      setSelectedCamera(null)
      fetchCameras()
    } catch {
      toast.error('Failed to assign camera')
    }
  }

  const handleUnassign = async (cameraId: number) => {
    try {
      await unassignCamera(cameraId)
      toast.success('Camera unassigned')
      fetchCameras()
    } catch {
      toast.error('Failed to unassign camera')
    }
  }

  const handleDelete = async (cameraId: number) => {
    try {
      await deleteCamera(cameraId)
      toast.success('Camera deleted')
      fetchCameras()
    } catch {
      toast.error('Failed to delete camera')
    }
  }

  const [confirmAction, setConfirmAction] = useState<{
    type: 'unassign' | 'delete'
    cameraId: number
    cameraName: string
  } | null>(null)

  if (loading) {
    console.log('CamerasPage: Still loading...')
    return <PageSpinner />
  }
  
  if (!workshopId) {
    return (
      <div className="p-6 min-h-screen">
        <div className="card p-8 text-center">
          <p className="text-white font-medium">No workshop selected</p>
          <p className="text-sm text-gray-500 mt-2">
            Please log in with a user account that has a workshop assigned.
          </p>
        </div>
      </div>
    )
  }

  return (
    <div className="p-6 min-h-screen">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-bold text-white">Camera Management</h1>
          <p className="text-sm text-gray-500 mt-1">
            Manage IP cameras and assign them to pits
          </p>
        </div>
        <div className="flex gap-2">
          <Button
            variant="secondary"
            leftIcon={<RefreshCw className="h-4 w-4" />}
            onClick={fetchCameras}
          >
            Refresh
          </Button>
          <Button
            leftIcon={<Search className="h-4 w-4" />}
            onClick={handleDiscover}
            isLoading={discovering}
          >
            {discovering ? 'Scanning...' : 'Discover Cameras'}
          </Button>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="card p-4">
          <p className="text-sm text-gray-500">Total</p>
          <p className="text-2xl font-bold text-white">{cameras.length}</p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-500">Online</p>
          <p className="text-2xl font-bold text-emerald-400">
            {cameras.filter((c) => c.is_online).length}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-500">Assigned</p>
          <p className="text-2xl font-bold text-electric-blue">
            {cameras.filter((c) => c.is_assigned).length}
          </p>
        </div>
        <div className="card p-4">
          <p className="text-sm text-gray-500">Discovered</p>
          <p className="text-2xl font-bold text-amber-400">
            {discoveredCameras.length}
          </p>
        </div>
      </div>

      {/* Discovered Cameras */}
      {discoveredCameras.length > 0 && (
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-white mb-4">
            New Cameras ({discoveredCameras.length})
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {discoveredCameras.map((camera) => (
              <div
                key={camera.id}
                className="card p-4 border border-amber-500/30 bg-amber-500/5"
              >
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-white font-medium">{camera.name}</h3>
                    <p className="text-sm text-gray-500">{camera.ip_address}</p>
                  </div>
                  <Badge variant="warning">New</Badge>
                </div>
                <p className="text-xs text-gray-500 mb-4">
                  Type: {camera.camera_type} | ID: {camera.device_id}
                </p>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    leftIcon={<MapPin className="h-3 w-3" />}
                    onClick={() => {
                      setSelectedCamera(camera)
                      setShowAssignModal(true)
                    }}
                  >
                    Assign to Pit
                  </Button>
                  <Button
                    size="sm"
                    variant="secondary"
                    leftIcon={<Eye className="h-3 w-3" />}
                    onClick={() => {
                      setSelectedCamera(camera)
                      setShowPreviewModal(true)
                    }}
                  >
                    Preview
                  </Button>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* All Cameras Table */}
      <h2 className="text-lg font-semibold text-white mb-4">
        All Cameras ({cameras.length})
      </h2>

      {cameras.length === 0 ? (
        <div className="card p-8 text-center">
          <Video className="h-12 w-12 text-gray-600 mx-auto mb-4" />
          <p className="text-white font-medium">No cameras found</p>
          <p className="text-sm text-gray-500 mt-2 mb-4">
            Use the Discover button to scan for cameras on your network.
          </p>
          <Button onClick={handleDiscover} isLoading={discovering}>
            Discover Cameras
          </Button>
        </div>
      ) : (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-white/5 border-b border-white/10">
                <tr>
                  <th className="text-left p-4 text-sm font-medium text-gray-400">
                    Camera
                  </th>
                  <th className="text-left p-4 text-sm font-medium text-gray-400">
                    IP Address
                  </th>
                  <th className="text-left p-4 text-sm font-medium text-gray-400">
                    Status
                  </th>
                  <th className="text-left p-4 text-sm font-medium text-gray-400">
                    Assigned To
                  </th>
                  <th className="text-left p-4 text-sm font-medium text-gray-400">
                    Stream
                  </th>
                  <th className="text-right p-4 text-sm font-medium text-gray-400">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {cameras.map((camera) => (
                  <tr key={camera.id} className="hover:bg-white/[0.02]">
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        <Video className="h-4 w-4 text-electric-blue" />
                        <span className="text-sm font-medium text-white">
                          {camera.name}
                        </span>
                      </div>
                      <p className="text-xs text-gray-500 mt-1">
                        {camera.device_id}
                      </p>
                    </td>
                    <td className="p-4 text-sm text-gray-400">
                      {camera.ip_address}
                    </td>
                    <td className="p-4">
                      <div className="flex items-center gap-2">
                        {camera.is_online ? (
                          <>
                            <Wifi className="h-3.5 w-3.5 text-emerald-400" />
                            <Badge variant="success">Online</Badge>
                          </>
                        ) : (
                          <>
                            <WifiOff className="h-3.5 w-3.5 text-gray-500" />
                            <Badge variant="danger">Offline</Badge>
                          </>
                        )}
                      </div>
                    </td>
                    <td className="p-4">
                      {camera.pit_name ? (
                        <div className="flex items-center gap-1.5">
                          <MapPin className="h-3.5 w-3.5 text-emerald-500" />
                          <span className="text-sm text-white">
                            {camera.pit_name}
                          </span>
                        </div>
                      ) : (
                        <span className="text-sm text-gray-500">-</span>
                      )}
                    </td>
                    <td className="p-4">
                      <span className="text-xs text-gray-500 truncate block max-w-[200px]">
                        {camera.primary_stream_url || '-'}
                      </span>
                    </td>
                    <td className="p-4 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          size="sm"
                          variant="ghost"
                          leftIcon={<Eye className="h-3 w-3" />}
                          onClick={() => {
                            setSelectedCamera(camera)
                            setShowPreviewModal(true)
                          }}
                        >
                          Preview
                        </Button>
                        {camera.is_assigned ? (
                          <Button
                            size="sm"
                            variant="outline"
                            leftIcon={<Unlink className="h-3 w-3" />}
                            onClick={() =>
                              setConfirmAction({
                                type: 'unassign',
                                cameraId: camera.id,
                                cameraName: camera.name,
                              })
                            }
                          >
                            Unassign
                          </Button>
                        ) : (
                          <Button
                            size="sm"
                            variant="outline"
                            leftIcon={<MapPin className="h-3 w-3" />}
                            onClick={() => {
                              setSelectedCamera(camera)
                              setShowAssignModal(true)
                            }}
                          >
                            Assign
                          </Button>
                        )}
                        <Button
                          size="sm"
                          variant="danger"
                          leftIcon={<Trash2 className="h-3 w-3" />}
                          onClick={() =>
                            setConfirmAction({
                              type: 'delete',
                              cameraId: camera.id,
                              cameraName: camera.name,
                            })
                          }
                        >
                          Delete
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Assign Camera Modal */}
      <Modal
        isOpen={showAssignModal && !!selectedCamera}
        onClose={() => {
          setShowAssignModal(false)
          setSelectedCamera(null)
        }}
        title="Assign Camera to Pit"
      >
        <div className="space-y-4">
          {selectedCamera && (
            <div className="bg-black/30 p-3 rounded-lg text-sm space-y-1">
              <p>
                <span className="text-gray-500">Camera:</span>{' '}
                <span className="text-white font-medium">
                  {selectedCamera.name}
                </span>
              </p>
              <p>
                <span className="text-gray-500">IP:</span>{' '}
                <span className="text-white">{selectedCamera.ip_address}</span>
              </p>
            </div>
          )}

          <div className="space-y-2 max-h-64 overflow-y-auto">
            {pits.length === 0 ? (
              <p className="text-sm text-gray-500 text-center py-4">
                No pits available. Create pits on the Dashboard first.
              </p>
            ) : (
              pits.map((pit) => (
                <button
                  key={pit.id}
                  className="w-full flex items-center justify-between px-4 py-3 rounded-lg border border-white/10 hover:border-electric-blue/50 hover:bg-white/5 transition-all text-left"
                  onClick={() => handleAssign(pit.id)}
                >
                  <span className="text-sm text-white font-medium">
                    Pit #{pit.pit_number} — {pit.name}
                  </span>
                  {pit.camera_ip && (
                    <Badge variant="warning">has camera</Badge>
                  )}
                </button>
              ))
            )}
          </div>

          <div className="pt-2">
            <Button
              variant="secondary"
              className="w-full"
              onClick={() => {
                setShowAssignModal(false)
                setSelectedCamera(null)
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      </Modal>

      {/* Preview Modal */}
      <Modal
        isOpen={showPreviewModal && !!selectedCamera}
        onClose={() => {
          setShowPreviewModal(false)
          setSelectedCamera(null)
        }}
        title={`Camera Preview: ${selectedCamera?.name ?? ''}`}
        size="xl"
      >
        <div className="space-y-4">
          <div className="bg-black rounded-lg overflow-hidden aspect-video">
            {selectedCamera?.primary_stream_url ? (
              <CameraStreamPlayer
                streamUrl={selectedCamera.primary_stream_url}
                className="w-full h-full"
              />
            ) : (
              <div className="flex items-center justify-center h-full text-gray-500">
                No stream URL available
              </div>
            )}
          </div>

          {selectedCamera && (
            <div className="text-sm space-y-1.5">
              <p>
                <span className="text-gray-500">Device ID:</span>{' '}
                <span className="text-white font-mono">
                  {selectedCamera.device_id}
                </span>
              </p>
              <p>
                <span className="text-gray-500">IP Address:</span>{' '}
                <span className="text-white">{selectedCamera.ip_address}</span>
              </p>
              <p>
                <span className="text-gray-500">Status:</span>{' '}
                {selectedCamera.is_online ? (
                  <Badge variant="success">Online</Badge>
                ) : (
                  <Badge variant="danger">Offline</Badge>
                )}
              </p>
              {selectedCamera.stream_urls && (
                <>
                  <p className="text-gray-500 pt-1">Stream URLs:</p>
                  <ul className="pl-4 space-y-0.5 text-gray-400">
                    {selectedCamera.stream_urls.webrtc?.main && (
                      <li>WebRTC: {selectedCamera.stream_urls.webrtc.main}</li>
                    )}
                    {selectedCamera.stream_urls.hls?.main && (
                      <li>HLS: {selectedCamera.stream_urls.hls.main}</li>
                    )}
                    {selectedCamera.stream_urls.rtsp?.main && (
                      <li>RTSP: {selectedCamera.stream_urls.rtsp.main}</li>
                    )}
                  </ul>
                </>
              )}
            </div>
          )}

          <Button
            className="w-full"
            onClick={() => {
              setShowPreviewModal(false)
              setSelectedCamera(null)
            }}
          >
            Close
          </Button>
        </div>
      </Modal>

      {/* Confirm Action Modal */}
      <Modal
        isOpen={!!confirmAction}
        onClose={() => setConfirmAction(null)}
        title={
          confirmAction?.type === 'delete'
            ? 'Delete Camera'
            : 'Unassign Camera'
        }
      >
        <div className="space-y-4">
          <p className="text-sm text-gray-400">
            {confirmAction?.type === 'delete'
              ? `Are you sure you want to delete "${confirmAction?.cameraName}"? This cannot be undone.`
              : `Are you sure you want to unassign "${confirmAction?.cameraName}" from its pit?`}
          </p>
          <div className="flex gap-3 pt-2">
            <Button
              variant="danger"
              className="flex-1"
              onClick={async () => {
                if (!confirmAction) return
                if (confirmAction.type === 'delete') {
                  await handleDelete(confirmAction.cameraId)
                } else {
                  await handleUnassign(confirmAction.cameraId)
                }
                setConfirmAction(null)
              }}
            >
              {confirmAction?.type === 'delete' ? 'Delete' : 'Unassign'}
            </Button>
            <Button variant="secondary" onClick={() => setConfirmAction(null)}>
              Cancel
            </Button>
          </div>
        </div>
      </Modal>
    </div>
  )
}
