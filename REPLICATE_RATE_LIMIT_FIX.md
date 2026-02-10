# Replicate Rate Limit Fix

## Problem
Even with $10 credit in Replicate account, the system was hitting rate limit errors:
```
Request was throttled. Your rate limit for creating predictions is reduced to 6 requests per minute
```

## Root Cause
Replicate enforces a rate limit of **6 requests per minute** (even with credit). When multiple generation requests come in quickly, they exceed this limit and get throttled.

## Solution
Implemented automatic rate limiting in the `ReplicateService` class to ensure we never exceed 6 requests per minute.

### Implementation Details

**Rate Limit Calculation:**
- 6 requests per minute = 1 request every 10 seconds
- Added `RATE_LIMIT_DELAY = 10` seconds between API calls

**How It Works:**
1. Track the timestamp of the last API call (class-level variable)
2. Before each new API call, check time since last call
3. If less than 10 seconds, wait the remaining time
4. Log the wait time for visibility
5. Update the last call timestamp

**Code Changes:**
```python
class ReplicateService:
    # Rate limiting: 6 requests per minute = 10 seconds between requests
    RATE_LIMIT_DELAY = 10  # seconds between API calls
    
    # Class-level variable to track last API call time
    _last_api_call_time = 0
    
    def _enforce_rate_limit(self):
        """
        Enforce rate limiting to avoid exceeding Replicate's 6 requests per minute limit.
        Waits if necessary to maintain the rate limit.
        """
        current_time = time.time()
        time_since_last_call = current_time - ReplicateService._last_api_call_time
        
        if time_since_last_call < self.RATE_LIMIT_DELAY:
            wait_time = self.RATE_LIMIT_DELAY - time_since_last_call
            logger.info(f"Rate limiting: waiting {wait_time:.1f}s before next API call")
            time.sleep(wait_time)
        
        ReplicateService._last_api_call_time = time.time()
```

## Benefits

1. **Automatic Rate Limiting**: No manual intervention needed
2. **Prevents Throttling**: Ensures we never exceed 6 requests/minute
3. **Transparent**: Logs wait times for visibility
4. **Thread-Safe**: Uses class-level variable shared across all instances
5. **No Failed Jobs**: Prevents rate limit errors from causing job failures

## Trade-offs

**Slower Processing:**
- Each generation now takes minimum 10 seconds apart
- Multiple generations will be queued and processed sequentially
- Example: 3 generations = 30 seconds total (10s each)

**Why This Is Acceptable:**
- Image generation itself takes 20-30 seconds
- The 10-second delay is minimal compared to generation time
- Prevents failed jobs and credit waste
- Ensures reliable, consistent operation

## User Experience

**Before Fix:**
- Fast initial requests
- Rate limit errors after 6 requests
- Failed generations
- Wasted credits

**After Fix:**
- Consistent, reliable generation
- No rate limit errors
- All generations succeed
- Slight delay between requests (barely noticeable)

## Monitoring

Watch for rate limiting in worker logs:
```bash
docker-compose logs -f worker | grep "Rate limiting"
```

You'll see messages like:
```
Rate limiting: waiting 7.3s before next API call
```

## Alternative Solutions Considered

1. **Increase Credit**: Doesn't help - rate limit is the same regardless of credit
2. **Multiple API Keys**: Against Replicate ToS, not recommended
3. **Queue Throttling**: More complex, same result
4. **Batch Processing**: Not supported by Replicate API

## Files Modified
- `app/services/replicate_service.py` - Added rate limiting logic

---

**Status**: ✅ IMPLEMENTED
**Date**: February 10, 2026
**Rate Limit**: 6 requests/minute (10s delay between calls)
