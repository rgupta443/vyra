# Sign-In Redirect Issue - Fixed

## Problem
After signing in, users were being redirected back to the sign-in page instead of the dashboard.

## Root Cause
The NextAuth credentials provider was not properly configured to:
1. Call the correct backend API endpoint (`/api/v1/auth/login` instead of `/auth/login`)
2. Fetch user information after login
3. Return the proper user object with all required fields

## Solution

### 1. Updated `frontend/auth.ts`
Fixed the credentials provider's `authorize` function to:
- Call `/api/v1/auth/login` to get the access token
- Use the access token to fetch user info from `/api/v1/auth/me`
- Return a complete user object with:
  - `id`: User ID
  - `email`: User email
  - `accessToken`: JWT token for API calls
  - `planType`: User's subscription plan
  - `credits`: Available credits

### 2. Updated JWT and Session Callbacks
Modified the callbacks to store and pass through:
- Access token
- Plan type
- Credits

### 3. Updated TypeScript Types
Extended `frontend/types/next-auth.d.ts` to include:
- `accessToken` in User, JWT, and Session interfaces
- `planType` in User, JWT, and Session interfaces
- `credits` in User, JWT, and Session interfaces

## Testing

### Backend API Verification
```bash
# Register a test user
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123","full_name":"Test User"}'

# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"testpass123"}'

# Get user info (use token from login response)
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

### Frontend Testing
1. Navigate to http://localhost:3000/auth/signin
2. Enter credentials
3. Click "Sign in"
4. Should redirect to http://localhost:3000/dashboard

## Next Steps

**IMPORTANT**: The frontend dev server needs to be restarted to pick up the changes:

```bash
cd frontend
# Stop the current dev server (Ctrl+C)
npm run dev
```

After restarting, the sign-in flow should work correctly.

## Files Changed
- `frontend/auth.ts` - Fixed credentials provider
- `frontend/types/next-auth.d.ts` - Extended type definitions

## Commit
```
Fix NextAuth credentials provider to properly authenticate with backend API
```
