'use client'

import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { FaceUpload } from '@/components/face/face-upload'
import api from '@/lib/api'

export default function DashboardPage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [currentFace, setCurrentFace] = useState<any>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin')
    }
  }, [status, router])

  useEffect(() => {
    if (session) {
      fetchCurrentFace()
    }
  }, [session])

  const fetchCurrentFace = async () => {
    try {
      const response = await api.get('/faces/current', {
        headers: {
          Authorization: `Bearer ${session?.user.accessToken}`,
        },
      })
      setCurrentFace(response.data)
    } catch (err) {
      // No face uploaded yet
      setCurrentFace(null)
    } finally {
      setLoading(false)
    }
  }

  const handleUploadSuccess = () => {
    fetchCurrentFace()
  }

  const handleRemoveFace = async () => {
    if (!confirm('Are you sure you want to remove your face? This will delete all associated data.')) {
      return
    }

    try {
      await api.delete('/faces/current', {
        headers: {
          Authorization: `Bearer ${session?.user.accessToken}`,
        },
      })
      setCurrentFace(null)
    } catch (err) {
      alert('Failed to remove face. Please try again.')
    }
  }

  if (status === 'loading' || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Dashboard</h1>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Face Management</h2>
            
            {currentFace ? (
              <div className="bg-white rounded-lg shadow-md p-6">
                <div className="mb-4">
                  <img
                    src={`${process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '')}${currentFace.image_url}`}
                    alt="Current face"
                    className="w-full aspect-square object-cover rounded-lg"
                  />
                </div>
                <div className="space-y-2 mb-4">
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Identity Strength:</span>{' '}
                    {(currentFace.identity_strength * 100).toFixed(1)}%
                  </p>
                  <p className="text-sm text-gray-600">
                    <span className="font-medium">Uploaded:</span>{' '}
                    {new Date(currentFace.created_at).toLocaleDateString()}
                  </p>
                </div>
                <button
                  onClick={handleRemoveFace}
                  className="w-full px-4 py-2 text-sm font-medium text-white bg-red-600 rounded-md hover:bg-red-700"
                >
                  Remove Face
                </button>
              </div>
            ) : (
              <FaceUpload onUploadSuccess={handleUploadSuccess} />
            )}
          </div>

          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Stats</h2>
            <div className="bg-white rounded-lg shadow-md p-6 space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Credits Remaining</span>
                <span className="text-2xl font-bold text-blue-600">--</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Generations This Month</span>
                <span className="text-2xl font-bold text-gray-900">--</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Current Plan</span>
                <span className="text-lg font-semibold text-gray-900">Free</span>
              </div>
            </div>

            {currentFace && (
              <div className="mt-6">
                <button
                  onClick={() => router.push('/generate')}
                  className="w-full px-6 py-3 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
                >
                  Start Generating
                </button>
              </div>
            )}
          </div>
        </div>
      </main>
    </div>
  )
}
