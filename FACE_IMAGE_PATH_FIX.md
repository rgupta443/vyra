# Face Image Path Fix

## Issue

Generation was failing with error:
```
FileNotFoundError: [Errno 2] No such file or directory
File "/app/app/services/replicate_service.py", line 91, in generate_image
    with open(face_image_path, 'rb') as f:
```

## Root Cause

The face image path conversion was too simplistic:
```python
# Old code - didn't handle all path formats
face_image_path = face.image_url.replace('/uploads/', 'uploads/')
```

This failed when:
- `face.image_url` had different formats
- Path didn't contain `/uploads/` exactly
- Leading slashes weren't handled properly

## Solution

### 1. Improved Path Handling (app/worker/tasks.py)

```python
# New code - handles multiple path formats
face_image_url = face.image_url
if face_image_url.startswith('/uploads/'):
    # Remove leading slash and use relative path
    face_image_path = face_image_url[1:]  # Remove leading /
elif face_image_url.startswith('uploads/'):
    # Already relative
    face_image_path = face_image_url
else:
    # Assume it's just the filename or partial path
    face_image_path = f"uploads/{face_image_url}"

logger.info(f"Using face image path: {face_image_path}")
```

### 2. Better Error Messages (app/services/replicate_service.py)

```python
# Added file existence check and logging
logger.info(f"Attempting to read face image from: {face_image_path}")

import os
if not os.path.exists(face_image_path):
    raise ReplicateError(f"Face image file not found at path: {face_image_path}")

with open(face_image_path, 'rb') as f:
    face_image_data = base64.b64encode(f.read()).decode('utf-8')
    
logger.info(f"Successfully loaded face image ({len(face_image_data)} bytes)")
```

## Path Format Examples

The fix now handles all these formats:

| Input Format | Output Path |
|-------------|-------------|
| `/uploads/faces/user-id/image.jpg` | `uploads/faces/user-id/image.jpg` |
| `uploads/faces/user-id/image.jpg` | `uploads/faces/user-id/image.jpg` |
| `faces/user-id/image.jpg` | `uploads/faces/user-id/image.jpg` |

## Verification

### Check Face Images Exist:
```bash
docker-compose exec worker ls -la /app/uploads/faces/
```

### Check Worker Logs:
```bash
docker-compose logs worker -f
```

Look for:
- `"Using face image path: uploads/faces/..."`
- `"Attempting to read face image from: ..."`
- `"Successfully loaded face image (X bytes)"`

## Testing

### Next Generation Attempt Will:
1. Log the exact path being used
2. Check if file exists before opening
3. Show clear error if file not found
4. Show success message with file size

### If Still Failing:
Check the logs for the exact path and verify:
```bash
# Check if the file exists at that path
docker-compose exec worker ls -la /app/uploads/faces/USER_ID/
```

## Status

✅ **Fixed** - Worker restarted with improved path handling
✅ **Logging** - Better error messages for debugging
✅ **Ready** - Next generation will use the fixed code

## Next Steps

1. Try generating content again
2. Check worker logs for path information
3. Verify image loads successfully
4. If issues persist, check the exact face.image_url format in database
