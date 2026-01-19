"""
Face management endpoints.
"""
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.dependencies import get_current_user, get_db
from app.models.user import User, PlanType
from app.models.face import Face
from app.schemas.face import FaceUploadResponse, FaceInfo, FaceDeleteResponse
from app.services.face_service import FaceService, FaceValidationError
from app.services.plan_service import PlanService

router = APIRouter()


@router.post("/upload", response_model=FaceUploadResponse)
async def upload_face(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and validate face image.
    
    Requirements: 3.1, 3.2
    - Validates image is front-facing and clear
    - Stores image securely with encryption
    - Prevents multiple active faces per user
    """
    try:
        # Check plan restrictions for face upload
        can_upload, restriction_message = FaceService.can_upload_face(db, str(current_user.id))
        if not can_upload:
            raise HTTPException(
                status_code=status.HTTP_402_PAYMENT_REQUIRED,
                detail={
                    "message": restriction_message,
                    "upgrade_message": PlanService.get_upgrade_message(PlanType(current_user.plan_type))
                }
            )
        
        # Check if user already has an active face
        existing_face = FaceService.get_user_active_face(db, str(current_user.id))
        if existing_face:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User already has an active face. Please delete the current face before uploading a new one."
            )
        
        # Validate upload file
        FaceService.validate_upload_file(file)
        
        # Read file content
        file_content = await file.read()
        
        # Validate image content and detect face
        image, metadata = FaceService.validate_image_content(file_content)
        face_info = FaceService.detect_and_validate_face(image)
        
        # Generate face embedding
        face_embedding = FaceService.generate_face_embedding(image, face_info["face_box"])
        
        # Encrypt embedding for storage
        encrypted_embedding = FaceService._encrypt_embedding(face_embedding)
        
        # Save image securely
        image_path = FaceService.save_image_securely(image, str(current_user.id))
        
        # Create face record in database with real embedding
        face = Face(
            user_id=current_user.id,
            image_url=image_path,
            embedding_data=encrypted_embedding,
            identity_strength=face_info["quality_score"],
            is_active=True
        )
        
        db.add(face)
        db.commit()
        db.refresh(face)
        
        # Cache the embedding for faster access
        FaceService.cache_embedding(str(face.id), face_embedding)
        
        # Return full URL for image access
        full_image_url = f"/uploads/{face.image_url}"
        
        return FaceUploadResponse(
            id=face.id,
            image_url=full_image_url,
            identity_strength=face.identity_strength,
            is_active=face.is_active,
            created_at=face.created_at,
            message="Face uploaded and validated successfully"
        )
        
    except FaceValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process face upload: {str(e)}"
        )


@router.get("/current", response_model=Optional[FaceInfo])
async def get_current_face(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current active face for the authenticated user."""
    face = FaceService.get_user_active_face(db, str(current_user.id))
    
    if not face:
        return None
    
    # Return full URL for image access
    full_image_url = f"/uploads/{face.image_url}"
    
    return FaceInfo(
        id=face.id,
        image_url=full_image_url,
        identity_strength=face.identity_strength,
        is_active=face.is_active,
        created_at=face.created_at
    )


@router.delete("/current", response_model=FaceDeleteResponse)
async def delete_current_face(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete current active face and associated files."""
    face = FaceService.get_user_active_face(db, str(current_user.id))
    
    if not face:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No active face found for user"
        )
    
    # Store face ID for response
    face_id = face.id
    
    # Invalidate cached embedding
    FaceService.invalidate_embedding_cache(str(face_id))
    
    # Delete face file from storage
    FaceService.delete_face_file(face.image_url)
    
    # Delete face record from database
    db.delete(face)
    db.commit()
    
    return FaceDeleteResponse(
        message="Face deleted successfully",
        deleted_face_id=face_id
    )