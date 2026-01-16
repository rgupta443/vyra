"""
Caching service for performance optimization.

This service provides caching functionality for frequently accessed data
to reduce database queries and improve response times.

Validates Requirements: System performance
"""
import logging
import json
from typing import Optional, Any, Callable
from functools import wraps
import hashlib

from app.core.redis import get_redis

logger = logging.getLogger(__name__)


class CacheService:
    """Service for caching frequently accessed data."""
    
    # Cache key prefixes
    USER_PREFIX = "user:"
    FACE_PREFIX = "face:"
    GENERATION_PREFIX = "generation:"
    PRESET_PREFIX = "preset:"
    CREDITS_PREFIX = "credits:"
    
    # Default TTL values (in seconds)
    DEFAULT_TTL = 300  # 5 minutes
    USER_TTL = 600  # 10 minutes
    FACE_TTL = 1800  # 30 minutes
    GENERATION_TTL = 60  # 1 minute (short for real-time updates)
    PRESET_TTL = 3600  # 1 hour (presets rarely change)
    CREDITS_TTL = 30  # 30 seconds (needs to be fresh)
    
    @staticmethod
    def _get_redis():
        """Get Redis connection."""
        try:
            return get_redis()
        except Exception as e:
            logger.error(f"Failed to get Redis connection: {e}")
            return None
    
    @staticmethod
    def _make_key(prefix: str, identifier: str) -> str:
        """
        Create a cache key.
        
        Args:
            prefix: Key prefix
            identifier: Unique identifier
            
        Returns:
            Cache key string
        """
        return f"{prefix}{identifier}"
    
    @staticmethod
    def get(key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found
        """
        redis_client = CacheService._get_redis()
        if not redis_client:
            return None
        
        try:
            value = redis_client.get(key)
            if value:
                return json.loads(value)
            return None
        except Exception as e:
            logger.error(f"Cache get error for key {key}: {e}")
            return None
    
    @staticmethod
    def set(key: str, value: Any, ttl: int = DEFAULT_TTL) -> bool:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            
        Returns:
            True if successful, False otherwise
        """
        redis_client = CacheService._get_redis()
        if not redis_client:
            return False
        
        try:
            serialized = json.dumps(value)
            redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.error(f"Cache set error for key {key}: {e}")
            return False
    
    @staticmethod
    def delete(key: str) -> bool:
        """
        Delete value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if successful, False otherwise
        """
        redis_client = CacheService._get_redis()
        if not redis_client:
            return False
        
        try:
            redis_client.delete(key)
            return True
        except Exception as e:
            logger.error(f"Cache delete error for key {key}: {e}")
            return False
    
    @staticmethod
    def delete_pattern(pattern: str) -> int:
        """
        Delete all keys matching a pattern.
        
        Args:
            pattern: Key pattern (e.g., "user:*")
            
        Returns:
            Number of keys deleted
        """
        redis_client = CacheService._get_redis()
        if not redis_client:
            return 0
        
        try:
            keys = redis_client.keys(pattern)
            if keys:
                return redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.error(f"Cache delete pattern error for {pattern}: {e}")
            return 0
    
    # User-specific cache methods
    
    @staticmethod
    def get_user(user_id: str) -> Optional[dict]:
        """Get cached user data."""
        key = CacheService._make_key(CacheService.USER_PREFIX, user_id)
        return CacheService.get(key)
    
    @staticmethod
    def set_user(user_id: str, user_data: dict) -> bool:
        """Cache user data."""
        key = CacheService._make_key(CacheService.USER_PREFIX, user_id)
        return CacheService.set(key, user_data, CacheService.USER_TTL)
    
    @staticmethod
    def invalidate_user(user_id: str) -> bool:
        """Invalidate user cache."""
        key = CacheService._make_key(CacheService.USER_PREFIX, user_id)
        return CacheService.delete(key)
    
    # Face-specific cache methods
    
    @staticmethod
    def get_face(face_id: str) -> Optional[dict]:
        """Get cached face data."""
        key = CacheService._make_key(CacheService.FACE_PREFIX, face_id)
        return CacheService.get(key)
    
    @staticmethod
    def set_face(face_id: str, face_data: dict) -> bool:
        """Cache face data."""
        key = CacheService._make_key(CacheService.FACE_PREFIX, face_id)
        return CacheService.set(key, face_data, CacheService.FACE_TTL)
    
    @staticmethod
    def invalidate_face(face_id: str) -> bool:
        """Invalidate face cache."""
        key = CacheService._make_key(CacheService.FACE_PREFIX, face_id)
        return CacheService.delete(key)
    
    # Generation-specific cache methods
    
    @staticmethod
    def get_generation(generation_id: str) -> Optional[dict]:
        """Get cached generation data."""
        key = CacheService._make_key(CacheService.GENERATION_PREFIX, generation_id)
        return CacheService.get(key)
    
    @staticmethod
    def set_generation(generation_id: str, generation_data: dict) -> bool:
        """Cache generation data."""
        key = CacheService._make_key(CacheService.GENERATION_PREFIX, generation_id)
        return CacheService.set(key, generation_data, CacheService.GENERATION_TTL)
    
    @staticmethod
    def invalidate_generation(generation_id: str) -> bool:
        """Invalidate generation cache."""
        key = CacheService._make_key(CacheService.GENERATION_PREFIX, generation_id)
        return CacheService.delete(key)
    
    # Preset-specific cache methods
    
    @staticmethod
    def get_preset(preset_type: str) -> Optional[dict]:
        """Get cached preset data."""
        key = CacheService._make_key(CacheService.PRESET_PREFIX, preset_type)
        return CacheService.get(key)
    
    @staticmethod
    def set_preset(preset_type: str, preset_data: dict) -> bool:
        """Cache preset data."""
        key = CacheService._make_key(CacheService.PRESET_PREFIX, preset_type)
        return CacheService.set(key, preset_data, CacheService.PRESET_TTL)
    
    @staticmethod
    def invalidate_all_presets() -> int:
        """Invalidate all preset caches."""
        pattern = f"{CacheService.PRESET_PREFIX}*"
        return CacheService.delete_pattern(pattern)
    
    # Credits-specific cache methods
    
    @staticmethod
    def get_credits(user_id: str) -> Optional[int]:
        """Get cached credit balance."""
        key = CacheService._make_key(CacheService.CREDITS_PREFIX, user_id)
        result = CacheService.get(key)
        return result if result is None else int(result)
    
    @staticmethod
    def set_credits(user_id: str, credits: int) -> bool:
        """Cache credit balance."""
        key = CacheService._make_key(CacheService.CREDITS_PREFIX, user_id)
        return CacheService.set(key, credits, CacheService.CREDITS_TTL)
    
    @staticmethod
    def invalidate_credits(user_id: str) -> bool:
        """Invalidate credit cache."""
        key = CacheService._make_key(CacheService.CREDITS_PREFIX, user_id)
        return CacheService.delete(key)


def cached(
    key_prefix: str,
    ttl: int = CacheService.DEFAULT_TTL,
    key_builder: Optional[Callable] = None
):
    """
    Decorator for caching function results.
    
    Args:
        key_prefix: Prefix for cache key
        ttl: Time to live in seconds
        key_builder: Optional function to build cache key from args
        
    Example:
        @cached("user_profile:", ttl=600)
        def get_user_profile(user_id: str):
            # Expensive database query
            return user_data
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            if key_builder:
                cache_key = key_prefix + key_builder(*args, **kwargs)
            else:
                # Default: use first argument as key
                if args:
                    cache_key = key_prefix + str(args[0])
                else:
                    # Hash all arguments if no positional args
                    key_data = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True)
                    key_hash = hashlib.md5(key_data.encode()).hexdigest()
                    cache_key = key_prefix + key_hash
            
            # Try to get from cache
            cached_result = CacheService.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Cache miss - call function
            logger.debug(f"Cache miss for {cache_key}")
            result = func(*args, **kwargs)
            
            # Store in cache
            if result is not None:
                CacheService.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator
