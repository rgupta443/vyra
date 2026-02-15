'use client'

import { useSession, signOut } from 'next-auth/react'
import { useRouter } from 'next/navigation'

export function SessionDisplay() {
  const { data: session, status } = useSession()
  const router = useRouter()

  if (status === 'loading') {
    return <div className="text-sm text-gray-500">Loading...</div>
  }

  if (!session) {
    return (
      <div className="flex gap-3">
        <button
          onClick={() => router.push('/auth/signin')}
          className="btn-ghost px-4 py-2 text-sm"
        >
          Sign In
        </button>
        <button
          onClick={() => router.push('/auth/signup')}
          className="btn-gradient px-4 py-2 text-sm"
        >
          Sign Up
        </button>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-4">
      <span className="text-sm text-gray-400">{session.user.email}</span>
      <button
        onClick={() => router.push('/dashboard')}
        className="btn-gradient px-4 py-2 text-sm"
      >
        Dashboard
      </button>
      <button
        onClick={() => signOut({ callbackUrl: '/' })}
        className="text-sm text-gray-500 hover:text-white transition-colors"
      >
        Sign Out
      </button>
    </div>
  )
}
