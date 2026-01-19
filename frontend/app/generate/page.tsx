'use client'

import { useSession } from 'next-auth/react'
import { useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import api from '@/lib/api'

type PresetType = 'LUXURY' | 'LIFESTYLE' | 'BEAUTY'
type FormatType = 'REEL_9_16' | 'FEED_4_5' | 'SQUARE_1_1'

const presets = [
  {
    id: 'LUXURY' as PresetType,
    name: 'Luxury',
    description: 'High-end fashion and luxury lifestyle',
    icon: '💎',
  },
  {
    id: 'LIFESTYLE' as PresetType,
    name: 'Lifestyle',
    description: 'Casual, everyday lifestyle content',
    icon: '☀️',
  },
  {
    id: 'BEAUTY' as PresetType,
    name: 'Beauty',
    description: 'Beauty and cosmetics focused',
    icon: '💄',
  },
]

const formats = [
  {
    id: 'REEL_9_16' as FormatType,
    name: 'Reels (9:16)',
    description: 'Vertical format for Instagram Reels',
    aspectRatio: '9/16',
  },
  {
    id: 'FEED_4_5' as FormatType,
    name: 'Feed (4:5)',
    description: 'Portrait format for Instagram Feed',
    aspectRatio: '4/5',
  },
  {
    id: 'SQUARE_1_1' as FormatType,
    name: 'Square (1:1)',
    description: 'Square format for Instagram Feed',
    aspectRatio: '1/1',
  },
]

export default function GeneratePage() {
  const { data: session, status } = useSession()
  const router = useRouter()
  const [selectedPreset, setSelectedPreset] = useState<PresetType>('LUXURY')
  const [selectedFormat, setSelectedFormat] = useState<FormatType>('FEED_4_5')
  const [generating, setGenerating] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (status === 'unauthenticated') {
      router.push('/auth/signin')
    }
  }, [status, router])

  const handleGenerate = async () => {
    if (!session) return

    setGenerating(true)
    setError(null)

    try {
      const response = await api.post(
        '/generate/image',
        {
          preset_type: selectedPreset.toLowerCase(),
          format_type: selectedFormat.toLowerCase(),
        },
        {
          headers: {
            Authorization: `Bearer ${session.user.accessToken}`,
          },
        }
      )

      // Redirect to results page with job ID
      router.push(`/results/${response.data.job_id}`)
    } catch (err: any) {
      if (err.response?.status === 400) {
        setError(err.response.data.detail || 'Please upload a face first')
      } else if (err.response?.status === 402) {
        setError('Insufficient credits. Please upgrade your plan.')
      } else {
        setError('Failed to start generation. Please try again.')
      }
    } finally {
      setGenerating(false)
    }
  }

  if (status === 'loading') {
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
          <h1 className="text-2xl font-bold text-gray-900">Generate Content</h1>
          <button
            onClick={() => router.push('/dashboard')}
            className="text-sm text-gray-600 hover:text-gray-900"
          >
            ← Back to Dashboard
          </button>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="space-y-8">
          {/* Preset Selection */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Preset</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {presets.map((preset) => (
                <button
                  key={preset.id}
                  onClick={() => setSelectedPreset(preset.id)}
                  className={`p-6 rounded-lg border-2 transition-all ${
                    selectedPreset === preset.id
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div className="text-4xl mb-3">{preset.icon}</div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    {preset.name}
                  </h3>
                  <p className="text-sm text-gray-600">{preset.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Format Selection */}
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Select Format</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {formats.map((format) => (
                <button
                  key={format.id}
                  onClick={() => setSelectedFormat(format.id)}
                  className={`p-6 rounded-lg border-2 transition-all ${
                    selectedFormat === format.id
                      ? 'border-blue-600 bg-blue-50'
                      : 'border-gray-200 bg-white hover:border-gray-300'
                  }`}
                >
                  <div
                    className="w-16 h-16 mx-auto mb-3 bg-gray-200 rounded"
                    style={{ aspectRatio: format.aspectRatio }}
                  />
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    {format.name}
                  </h3>
                  <p className="text-sm text-gray-600">{format.description}</p>
                </button>
              ))}
            </div>
          </div>

          {/* Error Display */}
          {error && (
            <div className="rounded-md bg-red-50 p-4">
              <p className="text-sm text-red-800">{error}</p>
            </div>
          )}

          {/* Generate Button */}
          <div className="bg-white rounded-lg shadow-md p-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-gray-900">Ready to Generate</h3>
                <p className="text-sm text-gray-600 mt-1">
                  Selected: {presets.find(p => p.id === selectedPreset)?.name} •{' '}
                  {formats.find(f => f.id === selectedFormat)?.name}
                </p>
              </div>
              <div className="text-right">
                <p className="text-sm text-gray-600">Cost</p>
                <p className="text-2xl font-bold text-gray-900">1 Credit</p>
              </div>
            </div>
            
            <button
              onClick={handleGenerate}
              disabled={generating}
              className="w-full px-6 py-3 text-lg font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {generating ? (
                <span className="flex items-center justify-center">
                  <svg
                    className="animate-spin -ml-1 mr-3 h-5 w-5 text-white"
                    xmlns="http://www.w3.org/2000/svg"
                    fill="none"
                    viewBox="0 0 24 24"
                  >
                    <circle
                      className="opacity-25"
                      cx="12"
                      cy="12"
                      r="10"
                      stroke="currentColor"
                      strokeWidth="4"
                    />
                    <path
                      className="opacity-75"
                      fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
                    />
                  </svg>
                  Generating...
                </span>
              ) : (
                'Generate Content'
              )}
            </button>
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 rounded-lg p-4">
            <h4 className="text-sm font-semibold text-blue-900 mb-2">What happens next?</h4>
            <ul className="text-sm text-blue-800 space-y-1">
              <li>• Your content will be generated using your uploaded face</li>
              <li>• AI will create a matching caption and hashtags</li>
              <li>• Location suggestions will be provided</li>
              <li>• Generation typically takes 30-60 seconds</li>
            </ul>
          </div>
        </div>
      </main>
    </div>
  )
}
