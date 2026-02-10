# Face Consistency Fix - Complete

## Problem Summary
User was uploading a girl's face image but getting images of the same guy every time, regardless of the uploaded face. The face was not being maintained across generated images.

## Root Cause
**Gemini (Imagen 3) does not support face consistency**. It's a text-to-image model that ignores the uploaded face image and generates random faces based only on the text prompt.

## Solution
Switched to **Replicate's InstantID model** (`zsxkib/instant-id`) which is specifically designed for face-consistent image generation.

### Key Differences:
- **Gemini**: Text-to-image only, generates random faces
- **Replicate InstantID**: Face-to-image, maintains uploaded face across different scenes/outfits

## Changes Made

### 1. Environment Configuration
```bash
IMAGE_GENERATION_PROVIDER=replicate
```

### 2. Cleared Stuck Jobs
- Flushed Redis database to remove all failed/stuck jobs
- These jobs were causing worker crashes with "Redis connection timeout" errors

### 3. Worker Restart
- Restarted worker container
- Worker now running stable without timeout errors

## Current Status
✅ System configured for Replicate with InstantID model
✅ $10 credit added to Replicate account (rate limit resolved)
✅ Redis queue cleared of stuck jobs
✅ Worker running stable
✅ Ready for testing

## Next Steps for User

### Test Face Consistency:
1. **Upload a fresh face image** in the UI
2. **Generate content** with different presets/scenes
3. **Verify** that the same face appears across all generated images
4. The uploaded face should be maintained while changing:
   - Outfits/clothing
   - Locations/backgrounds
   - Poses/angles
   - Lighting/style

### Expected Behavior:
- Same person (uploaded face) in every generated image
- Different scenes, outfits, and locations
- High identity strength (>0.95) maintained

## Technical Details

### Replicate InstantID Parameters:
- `ip_adapter_scale`: 0.8 (face consistency strength)
- `controlnet_conditioning_scale`: 0.8
- `identity_strength_threshold`: 0.95
- Model: `zsxkib/instant-id:dd5b2f35c0a0c3a8db2cbd90d1e5c88c40e9e3d1`

### Files Modified:
- `.env` - Set IMAGE_GENERATION_PROVIDER=replicate
- `docker-compose.yml` - Worker environment variables
- `app/services/replicate_service.py` - InstantID integration
- `app/worker/tasks.py` - Provider-specific thresholds

## Monitoring
Watch worker logs for any issues:
```bash
docker-compose logs -f worker
```

Check Redis queue status:
```bash
docker-compose exec redis redis-cli KEYS "rq:job:*"
```

## Troubleshooting

### If face still not consistent:
1. Check that face image uploaded successfully
2. Verify Replicate API token is valid
3. Check worker logs for errors
4. Ensure identity_strength > 0.95 in generation metadata

### If rate limit errors:
- Replicate requires $5+ credit for normal rate limits
- Current credit: $10 (should be sufficient)
- Rate limit: 6 requests/minute with <$5, higher with $5+

---

**Status**: ✅ READY FOR TESTING
**Date**: February 10, 2026
**Provider**: Replicate InstantID
**Credit**: $10
