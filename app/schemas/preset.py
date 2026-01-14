"""
Preset-related Pydantic schemas for request/response models.
"""
from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator
from datetime import datetime

from app.models.generation import PresetType


class PresetStyleParameters(BaseModel):
    """Style parameters for preset configuration."""
    identity_strength: float = Field(ge=0.95, le=1.0, description="Face identity consistency threshold")
    collage: bool = Field(default=False, description="Disable collage mode")
    sprite_mode: bool = Field(default=False, description="Disable sprite mode")
    quality: str = Field(default="high", description="Generation quality level")
    aspect_ratio: Optional[str] = Field(default=None, description="Aspect ratio override")
    
    @field_validator('identity_strength')
    @classmethod
    def validate_identity_strength(cls, v: float) -> float:
        """Ensure identity strength meets minimum requirement."""
        if v < 0.95:
            raise ValueError("Identity strength must be at least 0.95 for consistency")
        return v


class BrandSafetyRules(BaseModel):
    """Brand safety rules for content generation."""
    forbidden_terms: List[str] = Field(default_factory=list, description="Terms to avoid in prompts")
    forbidden_poses: List[str] = Field(default_factory=list, description="Poses to avoid")
    forbidden_expressions: List[str] = Field(default_factory=list, description="Expressions to avoid")
    forbidden_aesthetics: List[str] = Field(default_factory=list, description="Aesthetic styles to avoid")
    quality_standards: List[str] = Field(default_factory=list, description="Quality requirements")


class PresetConfigCreate(BaseModel):
    """Schema for creating a new preset configuration."""
    name: str = Field(min_length=1, max_length=100)
    prompt_template: str = Field(min_length=10, description="Template for generation prompts")
    style_parameters: Dict = Field(description="Style parameters as dict")
    brand_safety_rules: Dict = Field(description="Brand safety rules as dict")
    is_active: bool = Field(default=True)
    
    @field_validator('name')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate preset name."""
        if not v.strip():
            raise ValueError("Preset name cannot be empty")
        return v.strip().lower()
    
    @field_validator('style_parameters')
    @classmethod
    def validate_style_parameters(cls, v: Dict) -> Dict:
        """Validate style parameters structure."""
        # Ensure critical parameters are present
        if 'identity_strength' not in v:
            v['identity_strength'] = 0.95
        if 'collage' not in v:
            v['collage'] = False
        if 'sprite_mode' not in v:
            v['sprite_mode'] = False
        
        # Validate identity strength
        if v['identity_strength'] < 0.95:
            raise ValueError("Identity strength must be at least 0.95")
        
        # Ensure anti-collage enforcement
        if v['collage'] is not False:
            raise ValueError("Collage must be disabled for brand-safe content")
        if v['sprite_mode'] is not False:
            raise ValueError("Sprite mode must be disabled for brand-safe content")
        
        return v


class PresetConfigUpdate(BaseModel):
    """Schema for updating preset configuration."""
    prompt_template: Optional[str] = None
    style_parameters: Optional[Dict] = None
    brand_safety_rules: Optional[Dict] = None
    is_active: Optional[bool] = None


class PresetConfigResponse(BaseModel):
    """Schema for preset configuration response."""
    id: str
    name: str
    prompt_template: str
    style_parameters: Dict
    brand_safety_rules: Dict
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class PresetValidationResult(BaseModel):
    """Result of preset validation."""
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class PresetListResponse(BaseModel):
    """Schema for listing presets."""
    presets: List[PresetConfigResponse]
    total: int
