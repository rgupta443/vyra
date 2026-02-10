# Google Gemini (Imagen 3) Integration Guide

## Overview

Your system now supports **two image generation providers**:
1. **Replicate (InstantID)** - Best for face consistency
2. **Google Gemini (Imagen 3)** - High quality, good for general images

You can switch between them or test both to compare quality and cost.

## Setup Steps for Gemini

### 1. Get Google Cloud Project

If you already have a Google Cloud project with Vertex AI enabled, skip to step 2.

**Create new project:**
1. Go to https://console.cloud.google.com/
2. Click "Select a project" → "New Project"
3. Enter project name (e.g., "instagram-automation")
4. Click "Create"
5. Note your **Project ID** (not the name)

### 2. Enable Vertex AI API

1. Go to https://console.cloud.google.com/apis/library
2. Search for "Vertex AI API"
3. Click "Enable"
4. Wait for activation (1-2 minutes)

### 3. Create Service Account

1. Go to https://console.cloud.google.com/iam-admin/serviceaccounts
2. Click "Create Service Account"
3. Name: `instagram-worker`
4. Click "Create and Continue"
5. Grant role: **Vertex AI User**
6. Click "Continue" → "Done"

### 4. Generate Service Account Key

1. Click on the service account you just created
2. Go to "Keys" tab
3. Click "Add Key" → "Create new key"
4. Choose "JSON"
5. Click "Create"
6. Save the JSON file securely (e.g., `google-credentials.json`)

### 5. Update Configuration

**Option A: Using Service Account JSON File**

1. Place the JSON file in your project root or a secure location
2. Update `.env`:
```bash
GOOGLE_CLOUD_PROJECT_ID=your-actual-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_CREDENTIALS_PATH=./google-credentials.json
IMAGE_GENERATION_PROVIDER=gemini
```

**Option B: Using Default Credentials (if running on Google Cloud)**

If your app runs on Google Cloud (GCE, GKE, Cloud Run), you can use default credentials:
```bash
GOOGLE_CLOUD_PROJECT_ID=your-actual-project-id
GOOGLE_CLOUD_LOCATION=us-central1
GOOGLE_CLOUD_CREDENTIALS_PATH=
IMAGE_GENERATION_PROVIDER=gemini
```

### 6. Install Dependencies

```bash
# Rebuild Docker with new packages
docker-compose build --no-cache

# Or install locally
pip install google-cloud-aiplatform==1.38.1 google-auth==2.25.2
```

### 7. Restart Services

```bash
docker-compose down
docker-compose up -d
```

### 8. Verify Setup

```bash
# Check environment variables
docker-compose exec worker printenv | grep GOOGLE

# Should see:
# GOOGLE_CLOUD_PROJECT_ID=your-project-id
# GOOGLE_CLOUD_LOCATION=us-central1
# IMAGE_GENERATION_PROVIDER=gemini
```

## Switching Between Providers

### Use Replicate (InstantID):
```bash
# In .env file
IMAGE_GENERATION_PROVIDER=replicate
```

### Use Gemini (Imagen 3):
```bash
# In .env file
IMAGE_GENERATION_PROVIDER=gemini
```

After changing, restart the worker:
```bash
docker-compose restart worker
```

## Comparison: Replicate vs Gemini

| Feature | Replicate (InstantID) | Google Gemini (Imagen 3) |
|---------|----------------------|--------------------------|
| **Face Consistency** | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐ Good |
| **Image Quality** | ⭐⭐⭐⭐⭐ High | ⭐⭐⭐⭐⭐ High |
| **Setup Complexity** | ⭐⭐⭐⭐⭐ Easy | ⭐⭐⭐ Moderate |
| **Cost per Image** | $0.02-$0.07 | $0.01-$0.05 |
| **Generation Time** | 10-30 seconds | 15-40 seconds |
| **Best For** | Face-consistent content | General high-quality images |

## Testing Both Providers

### Test Replicate:
```bash
# Set in .env
IMAGE_GENERATION_PROVIDER=replicate

# Restart
docker-compose restart worker

# Generate content via UI
# Check face consistency
```

### Test Gemini:
```bash
# Set in .env
IMAGE_GENERATION_PROVIDER=gemini

# Restart
docker-compose restart worker

# Generate content via UI
# Compare quality and face consistency
```

### Compare Results:
1. Generate same content with both providers
2. Compare face consistency
3. Compare image quality
4. Compare generation time
5. Compare costs

## Cost Estimation

### Replicate (InstantID):
- **Model**: ~$0.0023 per second
- **Time**: 10-30 seconds
- **Cost**: ~$0.02-$0.07 per image

### Google Gemini (Imagen 3):
- **Model**: ~$0.02 per image (Vertex AI pricing)
- **Time**: 15-40 seconds
- **Cost**: ~$0.02-$0.04 per image

### Monthly Estimates:

| Usage | Replicate | Gemini |
|-------|-----------|--------|
| 100 images | $2-$7 | $2-$4 |
| 1000 images | $20-$70 | $20-$40 |
| 10000 images | $200-$700 | $200-$400 |

## Monitoring

### Check Current Provider:
```bash
docker-compose logs worker --tail 20 | grep "provider"
```

### Watch Generation:
```bash
docker-compose logs worker -f
```

Look for:
- `"Using image generation provider: replicate"` or `"gemini"`
- `"Generating image for face..."`
- `"Image generation successful..."`

## Troubleshooting

### Gemini: "Permission Denied"
**Solution:**
1. Verify Vertex AI API is enabled
2. Check service account has "Vertex AI User" role
3. Verify credentials file path is correct

### Gemini: "Project not found"
**Solution:**
1. Verify `GOOGLE_CLOUD_PROJECT_ID` is the Project ID (not name)
2. Check project exists in Google Cloud Console
3. Ensure billing is enabled for the project

### Gemini: "Quota exceeded"
**Solution:**
1. Check Vertex AI quotas: https://console.cloud.google.com/iam-admin/quotas
2. Request quota increase if needed
3. Or switch to Replicate temporarily

### Both: "Face consistency poor"
**Solution:**
- **Replicate**: Should be excellent (0.95+ identity strength)
- **Gemini**: May vary (0.85-0.95), not face-specific
- Consider using Replicate for face-critical content

## Best Practices

### For Face Consistency:
- **Use Replicate (InstantID)** - Specifically designed for it
- Upload high-quality face images
- Ensure face is front-facing and well-lit

### For Cost Optimization:
- **Use Gemini** for general images
- **Use Replicate** for face-critical content
- Monitor usage in both dashboards

### For Quality:
- Test both providers with your content
- Compare results side-by-side
- Choose based on your specific needs

## Support Resources

### Replicate:
- Docs: https://replicate.com/docs
- Model: https://replicate.com/zsxkib/instant-id
- Dashboard: https://replicate.com/account

### Google Gemini:
- Docs: https://cloud.google.com/vertex-ai/docs/generative-ai/image/overview
- Console: https://console.cloud.google.com/vertex-ai
- Pricing: https://cloud.google.com/vertex-ai/pricing

## Next Steps

1. ✅ **Set up Google Cloud** (if using Gemini)
2. ✅ **Choose provider** in .env
3. ✅ **Rebuild and restart** services
4. ✅ **Test generation** with both providers
5. ✅ **Compare results** and choose best fit
6. ✅ **Monitor costs** in both dashboards

---

**Current Status**: Both providers integrated and ready to use!

Switch between them anytime by changing `IMAGE_GENERATION_PROVIDER` in `.env` and restarting the worker.
