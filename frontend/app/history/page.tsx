'use client'

import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import api from '@/lib/api'
import Image from 'next/image'

interface Generation {
  id: string
  status: string
  image_url?: string
  caption?: string
  created_at: string
  preset_type: string
  format_type: string
}

export default function HistoryPage() {
  const { data: session, status: authStatus } = useSession()
  const router = useRouter()
  const [generations, setGenerations] = useState<Generation[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    if (authStatus === 'unauthenticated') {
      router.push('/auth/signin')
    }
  }, [authStatus, router])

  useEffect(() => {
    if (session) {
      fetchHistory()
    }
  }, [session])

  const fetchHistory = async () => {
    try {
      const response = await api.get('/generate/history', {
        headers: {
          Authorization: `Bearer ${session?.user.id}`,
        },
      })
      setGenerations(response.data)
    } catch (err) {
      console.error('Failed to fetch history:', err)
    } finally {
      setLoading(false)
    }
  }

  if (authStatus === 'loading' || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-gray-600">Loading...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Generation History</h1>
          <button
            onClick={() => router.push('/dashboard')}
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            ← Back to Dashboard
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {generations.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <p className="text-gray-600 mb-4">No generations yet</p>
            <button
              onClick={() => router.push('/generate')}
              className="px-6 py-3 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              Create Your First Generation
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {generations.map((gen) => (
              <div
                key={gen.id}
                onClick={() => router.push(`/results/${gen.id}`)}
                className="bg-white rounded-lg shadow-md overflow-hidden cursor-pointer hover:shadow-lg transition-shadow"
              >
                {gen.image_url && gen.status === 'COMPLETED' ? (
                  <div className="relative w-full aspect-[4/5]">
                    <Image
                      src={gen.image_url}
                      alt="Generated content"
                      fill
                      className="object-cover"
                    />
                  </div>
                ) : (
                  <div className="w-full aspect-[4/5] bg-gray-200 flex items-center justify-center">
                    <span className="text-gray-500">{gen.status}</span>
                  </div>
                )}
                <div className="p-4">
                  <p className="text-sm text-gray-600 mb-2">
                    {gen.preset_type} • {gen.format_type.replace('_', ' ')}
                  </p>
                  {gen.caption && (
                    <p className="text-sm text-gray-700 line-clamp-2 mb-2">
                      {gen.caption}
                    </p>
                  )}
                  <p className="text-xs text-gray-500">
                    {new Date(gen.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
            ))}
          </div>
        )}
      </main>
    </div>
  )
}
