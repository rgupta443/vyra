"""
Tests for preset configuration system.
"""
import pytest
from sqlalchemy.orm import Session

from app.models.generation import PresetType
from app.services.preset_service import PresetService
from app.schemas.preset import PresetConfigCreate


def test_initialize_default_presets(db: Session):
    """Test that default presets are initialized correctly."""
    presets = PresetService.initialize_default_presets(db)
    
    assert len(presets) == 3
    preset_names = [p.name for p in presets]
    assert "luxury" in preset_names
    assert "lifestyle" in preset_names
    assert "beauty" in preset_names
    
    # Verify all presets are active
    for preset in presets:
        assert preset.is_active is True
        assert preset.style_parameters['identity_strength'] == 0.95
        assert preset.style_parameters['collage'] is False
        assert preset.style_parameters['sprite_mode'] is False


def test_get_preset_by_type(db: Session):
    """Test retrieving preset by type."""
    # Initialize presets
    PresetService.initialize_default_presets(db)
    
    # Get luxury preset
    luxury = PresetService.get_preset_by_type(db, PresetType.LUXURY)
    assert luxury is not None
    assert luxury.name == "luxury"
    assert "luxury" in luxury.prompt_template.lower()
    
    # Get lifestyle preset
    lifestyle = PresetService.get_preset_by_type(db, PresetType.LIFESTYLE)
    assert lifestyle is not None
    assert lifestyle.name == "lifestyle"
    
    # Get beauty preset
    beauty = PresetService.get_preset_by_type(db, PresetType.BEAUTY)
    assert beauty is not None
    assert beauty.name == "beauty"


def test_validate_preset_parameters():
    """Test preset parameter validation."""
    # Valid parameters
    valid_params = {
        "identity_strength": 0.95,
        "collage": False,
        "sprite_mode": False,
        "quality": "high"
    }
    result = PresetService.validate_preset_parameters(valid_params)
    assert result.is_valid is True
    assert len(result.errors) == 0
    
    # Invalid identity strength
    invalid_params = {
        "identity_strength": 0.90,
        "collage": False,
        "sprite_mode": False
    }
    result = PresetService.validate_preset_parameters(invalid_params)
    assert result.is_valid is False
    assert len(result.errors) > 0
    
    # Collage enabled (should fail)
    invalid_params = {
        "identity_strength": 0.95,
        "collage": True,
        "sprite_mode": False
    }
    result = PresetService.validate_preset_parameters(invalid_params)
    assert result.is_valid is False
    assert any("collage" in error.lower() for error in result.errors)


def test_brand_safety_enforcement():
    """Test brand safety rule enforcement."""
    brand_safety_rules = PresetService.DEFAULT_BRAND_SAFETY_RULES
    
    # Safe prompt
    safe_prompt = "Professional portrait in elegant setting"
    is_safe, violation = PresetService.enforce_brand_safety(safe_prompt, brand_safety_rules)
    assert is_safe is True
    assert violation is None
    
    # Unsafe prompt with forbidden term
    unsafe_prompt = "Sexy portrait in bedroom"
    is_safe, violation = PresetService.enforce_brand_safety(unsafe_prompt, brand_safety_rules)
    assert is_safe is False
    assert violation is not None
    assert "sexy" in violation.lower()
    
    # Unsafe prompt with forbidden aesthetic
    unsafe_prompt = "Portrait with cheap filters"
    is_safe, violation = PresetService.enforce_brand_safety(unsafe_prompt, brand_safety_rules)
    assert is_safe is False
    assert violation is not None


def test_create_custom_preset(db: Session):
    """Test creating a custom preset."""
    preset_data = PresetConfigCreate(
        name="test_preset",
        prompt_template="Test portrait in professional setting",
        style_parameters={
            "identity_strength": 0.97,
            "collage": False,
            "sprite_mode": False,
            "quality": "high"
        },
        brand_safety_rules=PresetService.DEFAULT_BRAND_SAFETY_RULES
    )
    
    preset, error = PresetService.create_preset(db, preset_data)
    assert error is None
    assert preset is not None
    assert preset.name == "test_preset"
    assert preset.style_parameters['identity_strength'] == 0.97
    
    # Try to create duplicate (should fail)
    preset2, error2 = PresetService.create_preset(db, preset_data)
    assert preset2 is None
    assert error2 is not None
    assert "already exists" in error2.lower()


def test_get_all_active_presets(db: Session):
    """Test retrieving all active presets."""
    # Initialize default presets
    PresetService.initialize_default_presets(db)
    
    # Get all active presets
    presets = PresetService.get_all_active_presets(db)
    assert len(presets) >= 3
    
    # All should be active
    for preset in presets:
        assert preset.is_active is True
