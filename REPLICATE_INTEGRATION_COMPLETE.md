# Replicate Integration - Complete ✅

## Summary

Successfully integrated Replicate API for AI-powered Instagram content generation with face consistency using the InstantID model.

## Changes Made

### 1. New Files Created
- ✅ `app/services/replicate_service.py` - Replicate API client with InstantID integration
- ✅ `REPLICATE_SETUP.md` - Complete setup and usage guide
- ✅ `REPLICATE_INTEGRATION_COMPLETE.md` - This summary document

### 2. Files Updated
- ✅ `requirements.txt` - Added `replicate==0.22.0`
- ✅ `app/core/config.py` - Added `REPLICATE_API_TOKEN` configuration
- ✅ `app/worker/tasks.py` - Updated to use ReplicateService instead of NanoBananaService
- ✅ `docker-compose.yml` - Added REPLICATE_API_TOKEN environment variable
- ✅ `.env` - Added REPLICATE_API_TOKEN placeholder
- ✅ `.env.example` - Added REPLICATE_API_TOKEN example

## What You Need to Do Now

### Step 1: Get Replicate API Token
1. Go to: https://replicate.com/account/api-tokens
2. Sign up/in and create a token
3. Copy your token (starts with `r8_`)

### Step 2: Update Your `.env` File
Replace the placeholder with your actual token:
```bash
REPLICATE_API_TOKEN=r8_your_actual_token_here
```

### Step 3: Install Dependencies
```bash
# If using local Python environment:
pip install replicate==0.22.0

# If using Docker (recommended):
docker-compose build
```

### Step 4: Test with Demo Mode First
Demo mode is currently enabled in `docker-compose.yml`:
```yaml
DEMO_MODE=true  # Placeholder images for testing
```

This lets you test the entire pipeline without API costs.

### Step 5: Switch to Real API
Once you have your Replicate token:

1. Update `.env` with your token
2. In `docker-compose.yml`, change:
   ```yaml
   DEMO_MODE=false  # Use real Replicate API
   ```
3. Restart worker:
   ```bash
   docker-compose restart worker
   ```

## How It Works

### Face-Consistent Generation Flow:
1. User uploads face image → Stored in `uploads/` directory
2. User requests generation → Job queued
3. Worker picks up job → Calls ReplicateService
4. Replicate InstantID model:
   - Takes face image as reference
   - Generates new image with same face
   - Maintains identity consistency (0.95+ strength)
5. Result stored → UI displays completed generation

### Model Details:
- **Model**: InstantID by zsxkib
- **Purpose**: Face-consistent image generation
- **Identity Preservation**: High (0.95+ strength)
- **Generation Time**: 10-30 seconds
- **Cost**: ~$0.02-$0.07 per image

## Testing

### Current Status (Demo Mode):
```bash
docker-compose logs worker --tail 20
```
Should show: `"DEMO MODE: Returning fake image generation result"`

### After Adding Real Token:
```bash
# Check worker is using Replicate
docker-compose logs worker | grep -i replicate

# Test a generation from UI
# Should see: "Generating image for face..."
```

## Troubleshooting

### "Invalid API token"
- Verify token starts with `r8_`
- Check `.env` file has correct token
- Restart worker: `docker-compose restart worker`

### "Face image not found"
- Ensure face upload completed successfully
- Check `uploads/` directory has face images
- Verify face.image_url in database

### "Generation timeout"
- Replicate can take 10-30 seconds
- Check worker logs for errors
- Verify Replicate service status: https://status.replicate.com/

## Cost Estimation

Replicate charges per second of compute time:
- InstantID: ~$0.0023/second
- Average: 10-30 seconds per image
- **Cost per image: $0.02-$0.07**

For 100 images/month: ~$2-$7/month

## Next Steps

1. ✅ Get Replicate API token
2. ✅ Add to `.env` file
3. ✅ Test with demo mode (current state)
4. ✅ Switch to real API when ready
5. ✅ Monitor costs in Replicate dashboard

## Support

- **Replicate Docs**: https://replicate.com/docs
- **InstantID Model**: https://replicate.com/zsxkib/instant-id
- **Worker Logs**: `docker-compose logs worker -f`
- **API Logs**: `docker-compose logs api -f`

---

**Status**: ✅ Integration Complete - Ready for API Token

Once you add your Replicate API token and disable demo mode, you'll have real AI-powered Instagram content generation with face consistency!
