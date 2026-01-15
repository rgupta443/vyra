'use client'

interface ExportButtonsProps {
  imageUrl?: string
  caption?: string
  hashtags?: string[]
  location?: string
  generationId: string
}

export function ExportButtons({
  imageUrl,
  caption,
  hashtags,
  location,
  generationId,
}: ExportButtonsProps) {
  const handleDownloadImage = async () => {
    if (!imageUrl) return

    try {
      const response = await fetch(imageUrl)
      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `instagram-content-${generationId}.jpg`
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)
    } catch (err) {
      alert('Failed to download image')
    }
  }

  const handleCopyCaption = () => {
    if (!caption) return
    navigator.clipboard.writeText(caption)
    showCopyNotification('Caption copied!')
  }

  const handleCopyHashtags = () => {
    if (!hashtags || hashtags.length === 0) return
    const hashtagText = hashtags.map(tag => `#${tag}`).join(' ')
    navigator.clipboard.writeText(hashtagText)
    showCopyNotification('Hashtags copied!')
  }

  const handleCopyAll = () => {
    let text = ''
    
    if (caption) {
      text += caption + '\n\n'
    }
    
    if (hashtags && hashtags.length > 0) {
      text += hashtags.map(tag => `#${tag}`).join(' ')
    }
    
    if (location) {
      text += `\n\n📍 ${location}`
    }
    
    if (text) {
      navigator.clipboard.writeText(text)
      showCopyNotification('All content copied!')
    }
  }

  const showCopyNotification = (message: string) => {
    // Simple notification - could be replaced with a toast library
    const notification = document.createElement('div')
    notification.className = 'fixed bottom-4 right-4 bg-green-600 text-white px-6 py-3 rounded-lg shadow-lg z-50'
    notification.textContent = message
    document.body.appendChild(notification)
    
    setTimeout(() => {
      notification.remove()
    }, 2000)
  }

  return (
    <div className="space-y-3">
      {imageUrl && (
        <button
          onClick={handleDownloadImage}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
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
          Download Image
        </button>
      )}

      {caption && (
        <button
          onClick={handleCopyCaption}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
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
          Copy Caption
        </button>
      )}

      {hashtags && hashtags.length > 0 && (
        <button
          onClick={handleCopyHashtags}
          className="w-full flex items-center justify-center gap-2 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
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
              d="M7 20l4-16m2 16l4-16M6 9h14M4 15h14"
            />
          </svg>
          Copy Hashtags
        </button>
      )}

      <button
        onClick={handleCopyAll}
        className="w-full flex items-center justify-center gap-2 px-6 py-3 text-lg font-medium text-white bg-green-600 rounded-lg hover:bg-green-700"
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
            d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
          />
        </svg>
        Copy All for Instagram
      </button>
    </div>
  )
}
