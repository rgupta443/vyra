# Image URL Fix - Static File Serving

## Problem
Frontend was getting 404 errors when trying to load face images because:
1. Backend was returning relative paths like `faces/{user_id}/{filename}.jpg`
2. Frontend was trying to load from `http://localhost:3000/faces/...` (Next.js server)
3. No static file serving was configured on the backend

## Solution

### Backend Changes

#### 1. Added Static File Serving (`app/main.py`)
- Imported `StaticFiles` from FastAPI
- Created upload directory if it doesn't exist
- Mounted `/uploads` endpoint to serve files from the `uploads` directory
- Files are now accessible at `http://localhost:8000/uploads/faces/{user_id}/{filename}.jpg`

#### 2. Updated Face Endpoints (`app/api/v1/endpoints/faces.py`)
- Modified `/upload` endpoint to return full URL: `/uploads/{image_path}`
- Modified `/current` endpoint to return full URL: `/uploads/{image_path}`
- Backend now returns URLs like `/uploads/faces/{user_id}/{filename}.jpg`

### Frontend Changes

#### 1. Updated Dashboard (`frontend/app/dashboard/page.tsx`)
- Modified image src to prepend API base URL
- Uses `process.env.NEXT_PUBLIC_API_URL?.replace('/api/v1', '')` to get base URL
- Appends the image URL from backend
- Final URL: `http://localhost:8000/uploads/faces/{user_id}/{filename}.jpg`

## How It Works

1. **Upload Flow:**
   - User uploads face image
   - Backend saves to `uploads/faces/{user_id}/{filename}.jpg`
   - Backend returns `image_url: "/uploads/faces/{user_id}/{filename}.jpg"`
   - Frontend stores this URL

2. **Display Flow:**
   - Frontend fetches face data from `/api/v1/faces/current`
   - Gets `image_url: "/uploads/faces/{user_id}/{filename}.jpg"`
   - Prepends API base URL: `http://localhost:8000`
   - Final image src: `http://localhost:8000/uploads/faces/{user_id}/{filename}.jpg`
   - Browser loads image from backend static file server

## File Structure
```
uploads/
└── faces/
    └── {user_id}/
        └── {uuid}.jpg
```

## Testing
1. Restart backend server (to load static file serving)
2. Sign in to dashboard
3. Upload a face image
4. Image should display correctly without 404 errors
5. Check browser network tab - image should load from `http://localhost:8000/uploads/...`

## Status
✅ Backend static file serving configured
✅ Backend endpoints return full URLs
✅ Frontend dashboard updated to use correct URLs
⏳ Ready for testing
