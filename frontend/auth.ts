import NextAuth from "next-auth"
import Google from "next-auth/providers/google"
import Credentials from "next-auth/providers/credentials"

export const { handlers, signIn, signOut, auth } = NextAuth({
  providers: [
    Google({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET,
    }),
    Credentials({
      credentials: {
        email: { label: "Email", type: "email" },
        password: { label: "Password", type: "password" },
      },
      authorize: async (credentials) => {
        try {
          console.log("Attempting login with:", credentials.email)
          
          // Call backend login endpoint
          const loginResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          })

          console.log("Login response status:", loginResponse.status)

          if (!loginResponse.ok) {
            console.error("Login failed:", await loginResponse.text())
            return null
          }

          const { access_token } = await loginResponse.json()
          console.log("Got access token, fetching user info...")

          // Fetch user info using the access token
          const userResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/me`, {
            method: "GET",
            headers: {
              "Authorization": `Bearer ${access_token}`,
            },
          })

          console.log("User info response status:", userResponse.status)

          if (!userResponse.ok) {
            console.error("Failed to fetch user info:", await userResponse.text())
            return null
          }

          const user = await userResponse.json()
          console.log("User info retrieved:", { id: user.id, email: user.email })
          
          // Return user object with access token
          return {
            id: user.id,
            email: user.email,
            accessToken: access_token,
            planType: user.plan_type,
            credits: user.credits,
          }
        } catch (error) {
          console.error("Authentication error:", error)
          return null
        }
      },
    }),
  ],
  pages: {
    signIn: "/auth/signin",
  },
  callbacks: {
    async jwt({ token, user }) {
      if (user) {
        console.log("JWT callback - storing user data in token")
        token.id = user.id
        token.email = user.email
        token.accessToken = user.accessToken
        token.planType = user.planType
        token.credits = user.credits
      }
      return token
    },
    async session({ session, token }) {
      if (token) {
        console.log("Session callback - populating session from token")
        session.user.id = token.id as string
        session.user.email = token.email as string
        session.user.accessToken = token.accessToken as string
        session.user.planType = token.planType as string
        session.user.credits = token.credits as number
      }
      return session
    },
  },
  debug: true,
})
