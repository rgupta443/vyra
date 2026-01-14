"""
Authentication schemas for request/response models.
"""
from typing import Optional, TYPE_CHECKING
from pydantic import BaseModel, field_validator, ConfigDict
import re

if TYPE_CHECKING:
    pass


class UserResponse(BaseModel):
    """User response schema."""
    id: str
    email: str
    plan_type: str
    credits: int
    is_active: bool
    
    model_config = ConfigDict(from_attributes=True)


class UserRegister(BaseModel):
    """User registration request schema."""
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Simple email validation."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v


class UserLogin(BaseModel):
    """User login request schema."""
    email: str
    password: str
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Simple email validation."""
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, v):
            raise ValueError('Invalid email format')
        return v


class GoogleOAuthLogin(BaseModel):
    """Google OAuth login request schema."""
    google_token: str


class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str = "bearer"


class SessionResponse(BaseModel):
    """Session response schema."""
    session_id: str
    user: UserResponse