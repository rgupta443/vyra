"""
Authentication endpoints.
"""
from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status, Response, Cookie
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import create_access_token
from app.core.config import settings
from app.core.dependencies import get_current_user, get_current_user_session
from app.schemas.auth import UserRegister, UserLogin, GoogleOAuthLogin, Token, UserResponse, SessionResponse
from app.services.user_service import UserService
from app.services.oauth_service import OAuthService
from app.services.session_service import SessionService

router = APIRouter()


@router.post("/register", response_model=Token)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """User registration endpoint."""
    # Check if user already exists
    existing_user = UserService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = UserService.create_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """User login endpoint."""
    user = UserService.authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/session/register", response_model=SessionResponse)
async def register_with_session(
    user_data: UserRegister, 
    response: Response,
    db: Session = Depends(get_db)
):
    """User registration endpoint with session creation."""
    # Check if user already exists
    existing_user = UserService.get_user_by_email(db, user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    user = UserService.create_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to create user"
        )
    
    # Create session
    user_response = UserResponse(
        id=str(user.id),
        email=user.email,
        plan_type=user.plan_type,
        credits=user.credits,
        is_active=user.is_active
    )
    
    session_id = SessionService.create_session(
        str(user.id), 
        user_response.model_dump()
    )
    
    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax"
    )
    
    return SessionResponse(session_id=session_id, user=user_response)


@router.post("/session/login", response_model=SessionResponse)
async def login_with_session(
    user_data: UserLogin, 
    response: Response,
    db: Session = Depends(get_db)
):
    """User login endpoint with session creation."""
    user = UserService.authenticate_user(db, user_data.email, user_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Session"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create session
    user_response = UserResponse(
        id=str(user.id),
        email=user.email,
        plan_type=user.plan_type,
        credits=user.credits,
        is_active=user.is_active
    )
    
    session_id = SessionService.create_session(
        str(user.id), 
        user_response.model_dump()
    )
    
    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax"
    )
    
    return SessionResponse(session_id=session_id, user=user_response)


@router.post("/google", response_model=Token)
async def google_oauth_login(oauth_data: GoogleOAuthLogin, db: Session = Depends(get_db)):
    """Google OAuth login endpoint."""
    # Verify Google token
    user_info = await OAuthService.verify_google_token(oauth_data.google_token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
    
    # Create or get user
    user = UserService.create_or_get_google_user(
        db, user_info["email"], user_info["google_id"]
    )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/session/google", response_model=SessionResponse)
async def google_oauth_login_with_session(
    oauth_data: GoogleOAuthLogin, 
    response: Response,
    db: Session = Depends(get_db)
):
    """Google OAuth login endpoint with session creation."""
    # Verify Google token
    user_info = await OAuthService.verify_google_token(oauth_data.google_token)
    if not user_info:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Google token"
        )
    
    # Create or get user
    user = UserService.create_or_get_google_user(
        db, user_info["email"], user_info["google_id"]
    )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create session
    user_response = UserResponse(
        id=str(user.id),
        email=user.email,
        plan_type=user.plan_type,
        credits=user.credits,
        is_active=user.is_active
    )
    
    session_id = SessionService.create_session(
        str(user.id), 
        user_response.model_dump()
    )
    
    # Set session cookie
    response.set_cookie(
        key="session_id",
        value=session_id,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        httponly=True,
        secure=settings.ENVIRONMENT == "production",
        samesite="lax"
    )
    
    return SessionResponse(session_id=session_id, user=user_response)


@router.post("/logout")
async def logout(
    response: Response,
    session_id: str = Cookie(None, alias="session_id")
):
    """User logout endpoint."""
    # Delete session if it exists
    if session_id:
        SessionService.delete_session(session_id)
        # Clear session cookie
        response.delete_cookie(key="session_id")
    
    return {"message": "Successfully logged out"}


@router.post("/logout-all")
async def logout_all(
    response: Response,
    current_user = Depends(get_current_user)
):
    """Logout from all sessions."""
    # Delete all user sessions
    deleted_count = SessionService.delete_all_user_sessions(str(current_user.id))
    
    # Clear session cookie
    response.delete_cookie(key="session_id")
    
    return {"message": f"Successfully logged out from {deleted_count} sessions"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user = Depends(get_current_user)):
    """Get current user information."""
    return UserResponse(
        id=str(current_user.id),
        email=current_user.email,
        plan_type=current_user.plan_type,
        credits=current_user.credits,
        is_active=current_user.is_active
    )


@router.get("/session/validate")
async def validate_session(current_user = Depends(get_current_user_session)):
    """Validate current session."""
    return {
        "valid": True,
        "user_id": str(current_user.id),
        "email": current_user.email
    }