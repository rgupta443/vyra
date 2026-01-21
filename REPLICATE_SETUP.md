# Replicate Integration Setup

## Overview

This project now uses **Replicate** for AI-powered image generation with face consistency using the **InstantID** model.

## Setup Steps

### 1. Get Replicate API Token

1. Go to https://replicate.com/
2. Sign up or sign in
3. Navigate to https://replicate.com/account/api-tokens
4. Click "Create token"
5. Copy your API token

### 2. Add API Token to Environment

Update your `.env` file:

```bash
REPLICATE_API_TOKEN=r8_your_actual_token_here
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

Or in Docker:
```bash
docker-compose build
```

### 4. Update Docker Compose

The `docker-compose.yml` already includes the Replicate API token in the worker environment.

### 5. Disable Demo Mode

In `docker-compose.yml`, comment out or remove the `DEMO_MODE=true` line:

```yaml
worker:
  environment:
    # - DEMO_MODE=true  # Comment this out
    - REPLICATE_API_TOKEN=${REPLICATE_API_TOKEN}
```

### 6. Restart Services

```bash
docker-compose restart worker
```

## Model Information

**Model**: InstantID by zsxkib  
**Model ID**: `zsxkib/instant-id`  
**Purpose**: Face-consistent image generation

### Features:
- High face identity preservation
- Supports custom prompts
- Configurable image dimensions
- Style control via guidance scale
- Fast generation (typically 10-30 seconds)

### Parameters:
- `image`: Face reference image (base64 data URI)
- `prompt`: Text description of desired image
- `width/height`: Output dimensions (default: 1080x1350 for Instagram)
- `num_inference_steps`: Quality vs speed (default: 30)
- `guidance_scale`: Prompt adherence (default: 7.5)
- `ip_adapter_scale`: Face consistency strength (default: 0.8)

## Cost

Replicate charges per second of compute time:
- InstantID: ~$0.0023 per second
- Average generation: 10-30 seconds
- Cost per image: ~$0.02-$0.07

Check current pricing: https://replicate.com/pricing

## Testing

### With Demo Mode (No API calls):
```bash
# In docker-compose.yml
DEMO_MODE=true
```

### With Real API:
```bash
# In docker-compose.yml
# DEMO_MODE=true  # Commented out
REPLICATE_API_TOKEN=${REPLICATE_API_TOKEN}
```

## Troubleshooting

### "Invalid API token"
- Verify your token starts with `r8_`
- Check it's correctly set in `.env`
- Ensure no extra spaces or quotes

### "Model not found"
- The model ID is hardcoded in `app/services/replicate_service.py`
- If the model is deprecated, update to a newer version

### "Generation timeout"
- Increase `QUEUE_DEFAULT_TIMEOUT` in config
- Check Replicate service status: https://status.replicate.com/

### "Face not detected"
- Ensure uploaded face image is clear and well-lit
- Face should be front-facing
- Image should be at least 512x512 pixels

## Alternative Models

If you want to use a different Replicate model, update `MODEL_VERSION` in `app/services/replicate_service.py`:

```python
# Other face-consistent models:
MODEL_VERSION = "tencentarc/photomaker:ddfc2b08d209f9fa8c1eca692712918bd449f695dabb4a958da31802a9570fe4"
MODEL_VERSION = "lucataco/faceswap:9a4cc9d83a818c4b803c0a0e5b7e8c4f0e4e3b3b3b3b3b3b3b3b3b3b3b3b3b3b"
```

## Next Steps

1. Get your Replicate API token
2. Add it to `.env`
3. Rebuild Docker containers
4. Disable demo mode
5. Test image generation!

## Support

- Replicate Docs: https://replicate.com/docs
- InstantID Model: https://replicate.com/zsxkib/instant-id
- Project Issues: Check worker logs with `docker-compose logs worker`
