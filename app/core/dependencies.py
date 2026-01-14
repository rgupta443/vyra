"""
FastAPI dependencies for authentication and database access.
"""
from typing import Optional
from fastapi import Depends, HTTPException, status, Cookie, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.services.user_service import UserService
from app.services.session_service import SessionService

# HTTP Bearer token scheme
security = HTTPBearer()


def get_current_user_jwt(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token."""
    token = credentials.credentials
    payload = decode_access_token(token)
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user = UserService.get_user_by_id(db, user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


def get_current_user_session(
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from session cookie or Authorization header."""
    # Try session cookie first
    if session_id:
        user_id = SessionService.validate_session(session_id)
        if user_id:
            user = UserService.get_user_by_id(db, user_id)
            if user and user.is_active:
                # Extend session on successful validation
                SessionService.extend_session(session_id)
                return user
    
    # Try Authorization header with session ID
    if authorization and authorization.startswith("Session "):
        session_id = authorization.replace("Session ", "")
        user_id = SessionService.validate_session(session_id)
        if user_id:
            user = UserService.get_user_by_id(db, user_id)
            if user and user.is_active:
                SessionService.extend_session(session_id)
                return user
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid session or session expired",
        headers={"WWW-Authenticate": "Session"},
    )


def get_current_user(
    # Try JWT first, then session
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """Get current authenticated user from JWT token or session."""
    # Try JWT authentication first
    if credentials:
        try:
            return get_current_user_jwt(credentials, db)
        except HTTPException:
            pass
    
    # Try session authentication
    try:
        return get_current_user_session(session_id, authorization, db)
    except HTTPException:
        pass
    
    # If both fail, raise authentication error
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication credentials",
        headers={"WWW-Authenticate": "Bearer, Session"},
    )


def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(HTTPBearer(auto_error=False)),
    session_id: Optional[str] = Cookie(None, alias="session_id"),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Get current user if authenticated, otherwise return None."""
    try:
        return get_current_user(credentials, session_id, authorization, db)
    except HTTPException:
        return None