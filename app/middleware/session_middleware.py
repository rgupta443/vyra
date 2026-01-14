"""
Session validation middleware for automatic session management.
"""
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.services.session_service import SessionService


class SessionValidationMiddleware(BaseHTTPMiddleware):
    """Middleware to validate and extend sessions automatically."""
    
    def __init__(self, app, exclude_paths: list = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or [
            "/docs", "/redoc", "/openapi.json", "/health", "/",
            "/api/v1/auth/register", "/api/v1/auth/login", 
            "/api/v1/auth/session/register", "/api/v1/auth/session/login",
            "/api/v1/auth/google", "/api/v1/auth/session/google"
        ]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and validate session if present."""
        # Skip middleware for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Check for session cookie
        session_id = request.cookies.get("session_id")
        if session_id:
            # Validate and extend session
            user_id = SessionService.validate_session(session_id)
            if user_id:
                # Session is valid, extend it
                SessionService.extend_session(session_id)
                # Add user_id to request state for easy access
                request.state.user_id = user_id
                request.state.session_id = session_id
            else:
                # Invalid session, we could clear the cookie here
                # but we'll let the endpoint handle it
                pass
        
        response = await call_next(request)
        
        # If session was invalidated during request, clear cookie
        if hasattr(request.state, "clear_session_cookie"):
            response.delete_cookie(key="session_id")
        
        return response