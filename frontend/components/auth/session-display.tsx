'use client'

import { useSession, signOut } from 'next-auth/react'
import { useRouter } from 'next/navigation'

export function SessionDisplay() {
  const { data: session, status } = useSession()
  const router = useRouter()

  if (status === 'loading') {
    return <div className="text-sm text-gray-600">Loading...</div>
  }

  if (!session) {
    return (
      <div className="flex gap-4">
        <button
          onClick={() => router.push('/auth/signin')}
          className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
        >
          Sign In
        </button>
        <button
          onClick={() => router.push('/auth/signup')}
          className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700"
        >
          Sign Up
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-4">
      <span className="text-sm text-gray-700">{session.user.email}</span>
      <button
        onClick={() => signOut({ callbackUrl: '/' })}
        className="px-4 py-2 text-sm font-medium text-gray-700 hover:text-gray-900"
      >
        Sign Out
      </button>
    </div>
  )
}
