'use client'

import { useSession } from 'next-auth/react'

export default function TestSessionPage() {
  const { data: session, status } = useSession()

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 p-8">
      <div className="max-w-2xl w-full bg-white rounded-lg shadow-md p-6">
        <h1 className="text-2xl font-bold mb-4">Session Test Page</h1>
        
        <div className="space-y-4">
          <div>
            <strong>Status:</strong> {status}
          </div>
          
          <div>
            <strong>Session Data:</strong>
            <pre className="mt-2 p-4 bg-gray-100 rounded overflow-auto">
              {JSON.stringify(session, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </div>
  )
}
