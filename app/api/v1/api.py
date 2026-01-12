"""
Main API router that includes all endpoint routers.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, faces, generate, payments

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(faces.router, prefix="/faces", tags=["faces"])
api_router.include_router(generate.router, prefix="/generate", tags=["generation"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])