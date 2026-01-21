'use client'

import { useSession } from 'next-auth/react'
import { useRouter, useParams } from 'next/navigation'
import { useEffect, useState } from 'react'
import api from '@/lib/api'
import Image from 'next/image'

type GenerationStatus = 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'

interface Generation {
  id: string
  status: GenerationStatus
  image_url?: string
  caption?: string
  hashtags?: string[]
  location?: string
  created_at: string
  completed_at?: string
}

export default function ResultsPage() {
  const { data: session, status: authStatus } = useSession()
  const router = useRouter()
  const params = useParams()
  const jobId = params.jobId as string

  const [generation, setGeneration] = useState<Generation | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (authStatus === 'unauthenticated') {
      router.push('/auth/signin')
    }
  }, [authStatus, router])

  useEffect(() => {
    if (session && jobId) {
      fetchGenerationStatus()
      
      // Poll for status updates if not completed
      const interval = setInterval(() => {
        if (generation?.status === 'PENDING' || generation?.status === 'PROCESSING') {
          fetchGenerationStatus()
        }
      }, 3000)

      return () => clearInterval(interval)
    }
  }, [session, jobId, generation?.status])

  const fetchGenerationStatus = async () => {
    try {
      const response = await api.get(`/generate/status/${jobId}`, {
        headers: {
          Authorization: `Bearer ${session?.user.accessToken}`,
        },
      })
      setGeneration(response.data)
      setLoading(false)
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to fetch generation status')
      setLoading(false)
    }
  }

  const getStatusDisplay = () => {
    switch (generation?.status) {
      case 'PENDING':
        return { text: 'Queued', color: 'text-yellow-600', bg: 'bg-yellow-50' }
      case 'PROCESSING':
        return { text: 'Generating...', color: 'text-blue-600', bg: 'bg-blue-50' }
      case 'COMPLETED':
        return { text: 'Completed', color: 'text-green-600', bg: 'bg-green-50' }
      case 'FAILED':
        return { text: 'Failed', color: 'text-red-600', bg: 'bg-red-50' }
      default:
        return { text: 'Unknown', color: 'text-gray-600', bg: 'bg-gray-50' }
    }
  }

  const handleDownloadImage = async () => {
    if (!generation?.image_url) return

    try {
      const response = await fetch(generation.image_url)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `instagram-content-${generation.id}.jpg`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      alert('Failed to download image')
    }
  }

  const handleCopyCaption = () => {
    if (!generation?.caption) return
    navigator.clipboard.writeText(generation.caption)
    alert('Caption copied to clipboard!')
  }

  const handleCopyHashtags = () => {
    if (!generation?.hashtags) return
    const hashtagText = generation.hashtags.map(tag => `#${tag}`).join(' ')
    navigator.clipboard.writeText(hashtagText)
    alert('Hashtags copied to clipboard!')
  }

  const handleCopyAll = () => {
    if (!generation) return
    
    let text = ''
    if (generation.caption) {
      text += generation.caption + '\n\n'
    }
    if (generation.hashtags && generation.hashtags.length > 0) {
      text += generation.hashtags.map(tag => `#${tag}`).join(' ')
    }
    if (generation.location) {
      text += `\n\n📍 ${generation.location}`
    }
    
    navigator.clipboard.writeText(text)
    alert('All content copied to clipboard!')
  }

  if (authStatus === 'loading' || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4" />
          <p className="text-gray-600">Loading generation...</p>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <p className="text-red-600 mb-4">{error}</p>
          <button
            onClick={() => router.push('/generate')}
            className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
          >
            Try Again
          </button>
        </div>
      </div>
    )
  }

  const statusDisplay = getStatusDisplay()

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Generation Results</h1>
          <button
            onClick={() => router.push('/generate')}
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            Generate New
          </button>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Status Banner */}
        <div className={`${statusDisplay.bg} rounded-lg p-4 mb-6`}>
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <span className={`text-lg font-semibold ${statusDisplay.color}`}>
                {statusDisplay.text}
              </span>
              {(generation?.status === 'PENDING' || generation?.status === 'PROCESSING') && (
                <div className="ml-3 animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600" />
              )}
            </div>
            <span className="text-sm text-gray-600">
              Started {new Date(generation?.created_at || '').toLocaleString()}
            </span>
          </div>
        </div>

        {generation?.status === 'COMPLETED' && generation.image_url ? (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Image Display */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex justify-between items-center mb-4">
                <h2 className="text-xl font-semibold text-gray-900">Generated Image</h2>
                <button
                  onClick={handleDownloadImage}
                  className="flex items-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
                >
                  <svg
                    className="w-4 h-4"
                    fill="none"
                    stroke="currentColor"
                    viewBox="0 0 24 24"
                  >
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                    />
                  </svg>
                  Download
                </button>
              </div>
              <div className="relative w-full aspect-[4/5] rounded-lg overflow-hidden bg-gray-100">
                <Image
                  src={generation.image_url}
                  alt="Generated content"
                  fill
                  className="object-cover"
                  unoptimized
                />
              </div>
            </div>

            {/* Metadata Display */}
            <div className="space-y-6">
              {/* Caption */}
              {generation.caption && (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-lg font-semibold text-gray-900">Caption</h3>
                    <button
                      onClick={handleCopyCaption}
                      className="flex items-center gap-1 px-3 py-1 text-sm text-blue-600 hover:text-blue-700"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                        />
                      </svg>
                      Copy
                    </button>
                  </div>
                  <p className="text-gray-700 leading-relaxed">{generation.caption}</p>
                </div>
              )}

              {/* Hashtags */}
              {generation.hashtags && generation.hashtags.length > 0 && (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <div className="flex justify-between items-center mb-3">
                    <h3 className="text-lg font-semibold text-gray-900">Hashtags</h3>
                    <button
                      onClick={handleCopyHashtags}
                      className="flex items-center gap-1 px-3 py-1 text-sm text-blue-600 hover:text-blue-700"
                    >
                      <svg
                        className="w-4 h-4"
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                      >
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                        />
                      </svg>
                      Copy
                    </button>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {generation.hashtags.map((tag, index) => (
                      <span
                        key={index}
                        className="px-3 py-1 bg-blue-50 text-blue-700 rounded-full text-sm"
                      >
                        #{tag}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Location */}
              {generation.location && (
                <div className="bg-white rounded-lg shadow-md p-6">
                  <h3 className="text-lg font-semibold text-gray-900 mb-3">Location</h3>
                  <div className="flex items-center text-gray-700">
                    <svg
                      className="w-5 h-5 mr-2"
                      fill="none"
                      stroke="currentColor"
                      viewBox="0 0 24 24"
                    >
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                    </svg>
                    {generation.location}
                  </div>
                </div>
              )}

              {/* Copy All Button */}
              <button
                onClick={handleCopyAll}
                className="w-full px-6 py-3 text-lg font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 flex items-center justify-center gap-2"
              >
                <svg
                  className="w-5 h-5"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                  />
                </svg>
                Copy All for Instagram
              </button>
            </div>
          </div>
        ) : generation?.status === 'FAILED' ? (
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <div className="text-red-600 text-5xl mb-4">⚠️</div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">Generation Failed</h3>
            <p className="text-gray-600 mb-6">
              We encountered an error while generating your content. Your credit has been refunded.
            </p>
            <button
              onClick={() => router.push('/generate')}
              className="px-6 py-3 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700"
            >
              Try Again
            </button>
          </div>
        ) : (
          <div className="bg-white rounded-lg shadow-md p-8 text-center">
            <div className="animate-pulse">
              <div className="w-32 h-32 bg-gray-200 rounded-lg mx-auto mb-4" />
              <div className="h-4 bg-gray-200 rounded w-3/4 mx-auto mb-2" />
              <div className="h-4 bg-gray-200 rounded w-1/2 mx-auto" />
            </div>
            <p className="text-gray-600 mt-6">
              Your content is being generated. This usually takes 30-60 seconds...
            </p>
          </div>
        )}
      </main>
    </div>
  )
}
