# Sign-In Debugging Steps

## Changes Made

1. **Added Debug Logging** to `frontend/auth.ts`:
   - Logs when login is attempted
   - Logs API response statuses
   - Logs when user info is retrieved
   - Logs JWT and session callbacks
   - Enabled NextAuth debug mode

2. **Fixed NEXTAUTH_SECRET** in `frontend/.env.local`:
   - Generated a proper secret using `openssl rand -base64 32`
   - This is critical for session encryption

## Steps to Debug

### 1. Restart the Frontend Server

**IMPORTANT**: You MUST restart the frontend server for the `.env.local` changes to take effect:

```bash
# Stop the current server (Ctrl+C in the terminal running it)
cd frontend
npm run dev
```

### 2. Clear Browser Data

Before testing, clear your browser's cookies and local storage:

**Chrome/Edge:**
1. Open DevTools (F12)
2. Go to Application tab
3. Under Storage, click "Clear site data"
4. Refresh the page

**Firefox:**
1. Open DevTools (F12)
2. Go to Storage tab
3. Right-click on Cookies → Delete All
4. Right-click on Local Storage → Delete All
5. Refresh the page

### 3. Test Sign-In with Console Open

1. Open browser DevTools (F12)
2. Go to the Console tab
3. Navigate to http://localhost:3000/auth/signin
4. Enter credentials:
   - Email: `testlogin@example.com`
   - Password: `testpass123`
5. Click "Sign in"

### 4. Check Console Logs

You should see logs like:
```
Attempting login with: testlogin@example.com
Login response status: 200
Got access token, fetching user info...
User info response status: 200
User info retrieved: { id: '...', email: 'testlogin@example.com' }
JWT callback - storing user data in token
Session callback - populating session from token
```

### 5. Check Network Tab

In DevTools Network tab, look for:
1. **POST to `/api/v1/auth/login`** - Should return 200 with access_token
2. **GET to `/api/v1/auth/me`** - Should return 200 with user info
3. **POST to `/api/auth/callback/credentials`** - NextAuth callback
4. **GET to `/api/auth/session`** - Should return session data

### 6. Common Issues and Solutions

#### Issue: "Login response status: 404"
**Solution**: The API URL is wrong. Check `frontend/.env.local`:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

#### Issue: "User info response status: 401"
**Solution**: The access token isn't being passed correctly. Check the console logs.

#### Issue: Session is null after login
**Solution**: 
1. Make sure `NEXTAUTH_SECRET` is set in `frontend/.env.local`
2. Restart the frontend server
3. Clear browser cookies

#### Issue: Redirects to signin immediately
**Solution**:
1. Check if the session is being created (look for "Session callback" log)
2. Check browser cookies - should have `next-auth.session-token`
3. Try in incognito/private mode

### 7. Verify Backend is Working

Test the backend directly:

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"testlogin@example.com","password":"testpass123"}'

# Should return: {"access_token":"...","token_type":"bearer"}

# Get user info (replace TOKEN with the access_token from above)
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer TOKEN"

# Should return: {"id":"...","email":"testlogin@example.com","plan_type":"free","credits":5,"is_active":true}
```

### 8. Check Middleware

The middleware in `frontend/middleware.ts` protects these routes:
- `/dashboard/*`
- `/generate/*`
- `/profile/*`

If you're not authenticated, it will redirect to `/auth/signin`.

## What Should Happen

1. User enters credentials and clicks "Sign in"
2. Frontend calls `/api/v1/auth/login` → gets access token
3. Frontend calls `/api/v1/auth/me` with token → gets user info
4. NextAuth creates a session with the user data
5. User is redirected to `/dashboard`
6. Dashboard checks session → finds valid session → shows dashboard

## If Still Not Working

Please provide:
1. Console logs from the browser
2. Network tab showing the API calls
3. Any error messages

This will help identify exactly where the authentication flow is failing.
