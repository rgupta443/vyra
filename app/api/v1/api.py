"""
Main API router that includes all endpoint routers.
"""
from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, faces, generate, payments, plans, queue, presets

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(faces.router, prefix="/faces", tags=["faces"])
api_router.include_router(generate.router, prefix="/generate", tags=["generation"])
api_router.include_router(payments.router, prefix="/payments", tags=["payments"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(queue.router, prefix="/queue", tags=["queue"])
api_router.include_router(presets.router, prefix="/presets", tags=["presets"])