"""
Session management service using Redis for session persistence.
"""
import json
import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from app.core.redis import get_redis
from app.core.config import settings


class SessionService:
    """Service for managing user sessions with Redis."""
    
    SESSION_PREFIX = "session:"
    USER_SESSIONS_PREFIX = "user_sessions:"
    
    @staticmethod
    def create_session(user_id: str, user_data: Dict[str, Any]) -> str:
        """Create a new session for a user."""
        session_id = str(uuid.uuid4())
        redis_client = get_redis()
        
        session_data = {
            "user_id": user_id,
            "user_data": user_data,
            "created_at": datetime.utcnow().isoformat(),
            "last_accessed": datetime.utcnow().isoformat()
        }
        
        # Store session data
        session_key = f"{SessionService.SESSION_PREFIX}{session_id}"
        redis_client.setex(
            session_key,
            timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
            json.dumps(session_data)
        )
        
        # Track user sessions for logout-all functionality
        user_sessions_key = f"{SessionService.USER_SESSIONS_PREFIX}{user_id}"
        redis_client.sadd(user_sessions_key, session_id)
        redis_client.expire(user_sessions_key, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
        
        return session_id
    
    @staticmethod
    def get_session(session_id: str) -> Optional[Dict[str, Any]]:
        """Get session data by session ID."""
        redis_client = get_redis()
        session_key = f"{SessionService.SESSION_PREFIX}{session_id}"
        
        session_data = redis_client.get(session_key)
        if not session_data:
            return None
        
        try:
            data = json.loads(session_data)
            # Update last accessed time
            data["last_accessed"] = datetime.utcnow().isoformat()
            redis_client.setex(
                session_key,
                timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
                json.dumps(data)
            )
            return data
        except (json.JSONDecodeError, KeyError):
            return None
    
    @staticmethod
    def delete_session(session_id: str) -> bool:
        """Delete a specific session."""
        redis_client = get_redis()
        session_key = f"{SessionService.SESSION_PREFIX}{session_id}"
        
        # Get session data to find user_id
        session_data = redis_client.get(session_key)
        if session_data:
            try:
                data = json.loads(session_data)
                user_id = data.get("user_id")
                if user_id:
                    # Remove from user sessions set
                    user_sessions_key = f"{SessionService.USER_SESSIONS_PREFIX}{user_id}"
                    redis_client.srem(user_sessions_key, session_id)
            except (json.JSONDecodeError, KeyError):
                pass
        
        # Delete the session
        return redis_client.delete(session_key) > 0
    
    @staticmethod
    def delete_all_user_sessions(user_id: str) -> int:
        """Delete all sessions for a user."""
        redis_client = get_redis()
        user_sessions_key = f"{SessionService.USER_SESSIONS_PREFIX}{user_id}"
        
        # Get all session IDs for the user
        session_ids = redis_client.smembers(user_sessions_key)
        deleted_count = 0
        
        for session_id in session_ids:
            session_key = f"{SessionService.SESSION_PREFIX}{session_id.decode()}"
            if redis_client.delete(session_key) > 0:
                deleted_count += 1
        
        # Clear the user sessions set
        redis_client.delete(user_sessions_key)
        
        return deleted_count
    
    @staticmethod
    def validate_session(session_id: str) -> Optional[str]:
        """Validate session and return user_id if valid."""
        session_data = SessionService.get_session(session_id)
        if not session_data:
            return None
        
        return session_data.get("user_id")
    
    @staticmethod
    def extend_session(session_id: str) -> bool:
        """Extend session expiration time."""
        redis_client = get_redis()
        session_key = f"{SessionService.SESSION_PREFIX}{session_id}"
        
        # Check if session exists and extend it
        if redis_client.exists(session_key):
            redis_client.expire(session_key, timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES))
            return True
        
        return False