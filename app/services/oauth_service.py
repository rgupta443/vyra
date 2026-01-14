"""
OAuth service for Google authentication.
"""
from typing import Optional, Dict
import httpx

from app.core.config import settings


class OAuthService:
    """Service for OAuth authentication."""
    
    @staticmethod
    async def verify_google_token(token: str) -> Optional[Dict[str, str]]:
        """Verify Google OAuth token and return user info."""
        try:
            # Use Google's tokeninfo endpoint for verification
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"https://oauth2.googleapis.com/tokeninfo?access_token={token}"
                )
                
                if response.status_code != 200:
                    return None
                
                token_info = response.json()
                
                # Verify the token contains required fields
                if "email" not in token_info:
                    return None
                
                return {
                    "email": token_info["email"],
                    "google_id": token_info.get("sub", token_info.get("user_id", "")),
                    "name": token_info.get("name", ""),
                }
        except Exception:
            return None