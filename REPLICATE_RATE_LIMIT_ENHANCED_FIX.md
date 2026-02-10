# Replicate Rate Limit - Enhanced Fix

## Problem
Even after implementing 10-second delays, still getting rate limit errors:
```
Request was throttled. Your rate limit for creating predictions is reduced to 6 requests per minute 
with a burst of 1 requests while you have less than $5.0 in credit. Your rate limit resets in ~1s.
```

**Note**: User has $10 credit, but Replicate API still reports "less than $5.0" - this appears to be a Replicate API issue or credit recognition delay.

## Enhanced Solution

### 1. Increased Rate Limit Delay
**Changed from 10 seconds to 12 seconds** between API calls
- Provides extra buffer for API processing time
- Accounts for network latency
- More conservative approach to avoid edge cases

### 2. Enhanced Retry Logic
**Increased retry attempts and wait times:**
- Attempts: 3 → 5 (more chances to succeed)
- Wait multiplier: 2 → 3 (longer waits between retries)
- Min wait: 2s → 5s (start with longer wait)
- Max wait: 10s → 30s (allow much longer waits if needed)

**Exponential backoff example:**
- Retry 1: Wait 5 seconds
- Retry 2: Wait 15 seconds
- Retry 3: Wait 30 seconds
- Retry 4: Wait 30 seconds
- Retry 5: Wait 30 seconds

### 3. Rate Limit Error Detection
Added specific handling for rate limit errors:
```python
# Check if it's a rate limit error
error_str = str(e).lower()
if "throttled" in error_str or "rate limit" in error_str:
    logger.warning(f"Rate limit hit, will retry with exponential backoff: {e}")
    # Re-raise to trigger retry with exponential backoff
    raise ReplicateError(f"Rate limit exceeded: {e}")
```

This ensures rate limit errors are properly logged and retried with the enhanced backoff strategy.

## Why This Works

### Problem Analysis:
The error message "Your rate limit resets in ~1s" indicates we're hitting the limit at the exact moment. The issue is:
1. Multiple requests queued up before rate limiting was implemented
2. API processing time not accounted for
3. Network latency adds unpredictable delays
4. Replicate's credit recognition may be delayed

### Solution Benefits:
1. **12-second delay**: Guarantees we stay under 6 requests/minute (5 requests/minute max)
2. **5 retry attempts**: Handles transient rate limit issues
3. **Exponential backoff**: Automatically waits longer if rate limits persist
4. **Specific error handling**: Identifies and handles rate limit errors differently

## Expected Behavior

### First Request:
- Starts immediately
- No rate limiting needed

### Subsequent Requests:
- Waits 12 seconds since last request
- Logs: "Rate limiting: waiting X.Xs before next API call"
- Makes API call
- If rate limited: Retries with 5s, 15s, 30s delays

### If Rate Limit Hit:
1. First retry after 5 seconds
2. Second retry after 15 seconds
3. Third retry after 30 seconds
4. Should succeed by then (rate limit resets every minute)

## Monitoring

Watch for rate limiting in logs:
```bash
docker-compose logs -f worker | grep -E "Rate limiting|throttled"
```

You should see:
```
Rate limiting: waiting 12.0s before next API call
```

If rate limited:
```
Rate limit hit, will retry with exponential backoff
```

## Troubleshooting

### If Still Getting Rate Limit Errors:

1. **Check Replicate Account**:
   - Verify $10 credit is actually applied
   - Check billing page for pending charges
   - Ensure payment method is valid

2. **Wait 60 Seconds**:
   - Replicate rate limits reset every minute
   - Clear Redis queue: `docker-compose exec redis redis-cli FLUSHDB`
   - Wait 60 seconds
   - Try again

3. **Check for Multiple Workers**:
   - Ensure only one worker is running
   - Multiple workers share the same rate limit
   - Check: `docker ps | grep worker`

4. **Verify API Token**:
   - Ensure new token is active
   - Old token should be disabled
   - Check: `docker-compose exec worker printenv | grep REPLICATE`

## Files Modified
- `app/services/replicate_service.py`:
  - Increased RATE_LIMIT_DELAY: 10 → 12 seconds
  - Enhanced retry logic: 3 → 5 attempts
  - Added rate limit error detection
  - Increased exponential backoff times

## Next Steps

1. **Clear all queued jobs**: ✅ Done
2. **Restart worker**: ✅ Done
3. **Wait 60 seconds** before testing (let rate limit reset)
4. **Test with single generation** first
5. **Monitor logs** for rate limiting messages

---

**Status**: ✅ ENHANCED FIX APPLIED
**Date**: February 10, 2026
**Rate Limit**: 5 requests/minute (12s delay between calls)
**Retry Strategy**: 5 attempts with exponential backoff (5s → 30s)
