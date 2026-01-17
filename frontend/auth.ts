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
          // Call backend login endpoint
          const loginResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/login`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          })

          if (!loginResponse.ok) {
            return null
          }

          const { access_token } = await loginResponse.json()

          // Fetch user info using the access token
          const userResponse = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/auth/me`, {
            method: "GET",
            headers: {
              "Authorization": `Bearer ${access_token}`,
            },
          })

          if (!userResponse.ok) {
            return null
          }

          const user = await userResponse.json()
          
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
        session.user.id = token.id as string
        session.user.email = token.email as string
        session.user.accessToken = token.accessToken as string
        session.user.planType = token.planType as string
        session.user.credits = token.credits as number
      }
      return session
    },
  },
})
