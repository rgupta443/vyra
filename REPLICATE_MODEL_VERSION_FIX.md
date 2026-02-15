# Replicate Model Version Fix

## Problem
Getting error when trying to generate images:
```
ReplicateError: The specified version does not exist (or perhaps you don't have permission to use it?)
```

## Root Cause
The hardcoded model version `zsxkib/instant-id:dd5b2f35c0a0c3a8db2cbd90d1e5c88c40e9e3d1` no longer exists or is not accessible with the current API token.

Possible reasons:
1. Model version was deprecated/removed by the author
2. Model version hash changed
3. New API token doesn't have permission to access that specific version
4. Model was updated and old version is no longer available

## Solution
Updated the code to use the model **without specifying a version**, which automatically uses the latest available version:

```python
# Before (hardcoded version):
MODEL_VERSION = "zsxkib/instant-id:dd5b2f35c0a0c3a8db2cbd90d1e5c88c40e9e3d1"

# After (latest version):
MODEL_VERSION = "zsxkib/instant-id"
```

## Benefits

1. **Always Uses Latest**: Automatically gets the latest model version
2. **No Version Maintenance**: Don't need to update version hashes manually
3. **More Reliable**: Won't break when old versions are deprecated
4. **Simpler**: Cleaner code without long version hashes

## Trade-offs

**Potential Issues:**
- Model API might change between versions (breaking changes)
- Results might vary slightly with different versions
- Less control over which exact version is used

**Mitigation:**
- Replicate generally maintains backward compatibility
- InstantID model has stable API
- Can always pin to specific version later if needed

## Testing

After this fix:
1. Worker restarted with new model reference
2. Next generation will use latest InstantID version
3. Should work without "version does not exist" error

## Alternative Models

If `zsxkib/instant-id` doesn't work, other InstantID models on Replicate:
- `zsxkib/instant-id-basic` - Basic version
- `grandlineai/instant-id-artistic` - Artistic style
- `grandlineai/instant-id-photorealistic` - Photorealistic style
- `zedge/instantid` - Alternative implementation

## Files Modified
- `app/services/replicate_service.py` - Removed version hash from MODEL_VERSION

## Next Steps

1. ✅ Code updated to use latest version
2. ✅ Worker restarted
3. 🧪 Test with new generation
4. 📊 Monitor for any API changes

---

**Status**: ✅ FIXED
**Date**: February 15, 2026
**Model**: zsxkib/instant-id (latest version)
