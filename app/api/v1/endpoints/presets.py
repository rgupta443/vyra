"""
Preset configuration API endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.dependencies import get_db, get_current_user
from app.models.user import User
from app.models.generation import PresetType
from app.services.preset_service import PresetService
from app.schemas.preset import (
    PresetConfigResponse,
    PresetListResponse,
    PresetConfigCreate,
    PresetConfigUpdate,
    PresetValidationResult
)

router = APIRouter()


@router.get("/", response_model=PresetListResponse)
def list_presets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all active preset configurations.
    
    Returns available presets for content generation.
    """
    presets = PresetService.get_all_active_presets(db)
    
    return PresetListResponse(
        presets=[PresetConfigResponse.model_validate(p) for p in presets],
        total=len(presets)
    )


@router.get("/{preset_type}", response_model=PresetConfigResponse)
def get_preset(
    preset_type: PresetType,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a specific preset configuration by type.
    
    Args:
        preset_type: Type of preset (luxury, lifestyle, beauty)
    """
    preset = PresetService.get_preset_by_type(db, preset_type)
    
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset '{preset_type.value}' not found"
        )
    
    return PresetConfigResponse.model_validate(preset)


@router.post("/validate", response_model=PresetValidationResult)
def validate_preset_parameters(
    style_parameters: dict,
    current_user: User = Depends(get_current_user)
):
    """
    Validate preset style parameters for brand safety and technical requirements.
    
    Args:
        style_parameters: Dictionary of style parameters to validate
    """
    return PresetService.validate_preset_parameters(style_parameters)


@router.post("/", response_model=PresetConfigResponse, status_code=status.HTTP_201_CREATED)
def create_preset(
    preset_data: PresetConfigCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new preset configuration.
    
    Note: This endpoint is typically for admin use only.
    """
    preset, error = PresetService.create_preset(db, preset_data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return PresetConfigResponse.model_validate(preset)


@router.put("/{preset_id}", response_model=PresetConfigResponse)
def update_preset(
    preset_id: UUID,
    preset_data: PresetConfigUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update an existing preset configuration.
    
    Note: This endpoint is typically for admin use only.
    """
    preset, error = PresetService.update_preset(db, preset_id, preset_data)
    
    if error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )
    
    return PresetConfigResponse.model_validate(preset)


@router.post("/initialize", response_model=PresetListResponse)
def initialize_default_presets(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Initialize default preset configurations.
    
    Creates the default Luxury, Lifestyle, and Beauty presets if they don't exist.
    Note: This endpoint is typically for admin use only.
    """
    presets = PresetService.initialize_default_presets(db)
    
    return PresetListResponse(
        presets=[PresetConfigResponse.model_validate(p) for p in presets],
        total=len(presets)
    )
