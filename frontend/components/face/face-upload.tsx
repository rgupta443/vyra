'use client'

import { useState, useRef } from 'react'
import { useSession } from 'next-auth/react'
import api from '@/lib/api'
import Image from 'next/image'

interface FaceUploadProps {
  onUploadSuccess?: () => void
}

export function FaceUpload({ onUploadSuccess }: FaceUploadProps) {
  const { data: session } = useSession()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [uploading, setUploading] = useState(false)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (!file) return

    // Validate file type
    if (!file.type.startsWith('image/')) {
      setError('Please select an image file')
      return
    }

    // Validate file size (max 10MB)
    if (file.size > 10 * 1024 * 1024) {
      setError('File size must be less than 10MB')
      return
    }

    setSelectedFile(file)
    setError(null)
    setSuccess(false)

    // Create preview
    const reader = new FileReader()
    reader.onloadend = () => {
      setPreview(reader.result as string)
    }
    reader.readAsDataURL(file)
  }

  const handleUpload = async () => {
    if (!selectedFile || !session) return

    setUploading(true)
    setError(null)
    setProgress(0)

    try {
      const formData = new FormData()
      formData.append('file', selectedFile)

      // Simulate progress for better UX
      const progressInterval = setInterval(() => {
        setProgress((prev) => Math.min(prev + 10, 90))
      }, 200)

      const response = await api.post('/faces/upload', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
          Authorization: `Bearer ${session.user.accessToken}`,
        },
      })

      clearInterval(progressInterval)
      setProgress(100)
      setSuccess(true)
      
      if (onUploadSuccess) {
        onUploadSuccess()
      }

      // Reset after success
      setTimeout(() => {
        setSelectedFile(null)
        setPreview(null)
        setProgress(0)
      }, 2000)
    } catch (err: any) {
      setError(
        err.response?.data?.detail || 
        'Failed to upload face. Please ensure the image is clear and front-facing.'
      )
    } finally {
      setUploading(false)
    }
  }

  const handleClear = () => {
    setSelectedFile(null)
    setPreview(null)
    setError(null)
    setSuccess(false)
    setProgress(0)
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  return (
    <div className="w-full max-w-md mx-auto">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Upload Your Face</h3>
        
        {!preview ? (
          <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center hover:border-blue-500 transition-colors">
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleFileSelect}
              className="hidden"
              id="face-upload"
            />
            <label
              htmlFor="face-upload"
              className="cursor-pointer flex flex-col items-center"
            >
              <svg
                className="w-12 h-12 text-gray-400 mb-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
                />
              </svg>
              <span className="text-sm text-gray-600 mb-2">
                Click to upload or drag and drop
              </span>
              <span className="text-xs text-gray-500">
                PNG, JPG up to 10MB
              </span>
            </label>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="relative w-full aspect-square rounded-lg overflow-hidden bg-gray-100">
              <Image
                src={preview}
                alt="Face preview"
                fill
                className="object-cover"
              />
            </div>

            {uploading && (
              <div className="space-y-2">
                <div className="flex justify-between text-sm text-gray-600">
                  <span>Uploading...</span>
                  <span>{progress}%</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>
            )}

            {success && (
              <div className="rounded-md bg-green-50 p-4">
                <p className="text-sm text-green-800">
                  ✓ Face uploaded successfully!
                </p>
              </div>
            )}

            {error && (
              <div className="rounded-md bg-red-50 p-4">
                <p className="text-sm text-red-800">{error}</p>
              </div>
            )}

            <div className="flex gap-3">
              <button
                onClick={handleUpload}
                disabled={uploading || success}
                className="flex-1 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {uploading ? 'Uploading...' : success ? 'Uploaded!' : 'Upload'}
              </button>
              <button
                onClick={handleClear}
                disabled={uploading}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Clear
              </button>
            </div>
          </div>
        )}

        <div className="mt-4 text-xs text-gray-500">
          <p className="mb-2">Requirements:</p>
          <ul className="list-disc list-inside space-y-1">
            <li>Clear, front-facing photo</li>
            <li>Good lighting and focus</li>
            <li>Only one face in the image</li>
            <li>No sunglasses or face coverings</li>
          </ul>
        </div>
      </div>
    </div>
  )
}
