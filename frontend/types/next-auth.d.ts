import { DefaultSession } from "next-auth"

declare module "next-auth" {
  interface Session {
    user: {
      id: string
      email: string
      accessToken: string
      planType: string
      credits: number
    } & DefaultSession["user"]
  }

  interface User {
    id: string
    email: string
    accessToken: string
    planType: string
    credits: number
  }
}

declare module "next-auth/jwt" {
  interface JWT {
    id: string
    email: string
    accessToken: string
    planType: string
    credits: number
  }
}
