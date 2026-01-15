"""
Tests for Nano Banana API client and format compliance services.
"""
import pytest
from app.services.nano_banana_service import NanoBananaService
from app.services.format_compliance_service import (
    FormatComplianceService,
    InstagramFormat,
    FormatValidationResult
)
from PIL import Image
import io


class TestNanoBananaService:
    """Tests for Nano Banana API client."""
    
    def test_anti_collage_enforcement(self):
        """Test that anti-collage parameters are enforced."""
        service = NanoBananaService()
        
        # Test that collage=False is enforced
        params = {"quality": "high"}
        result = service._enforce_anti_collage_parameters(params)
        
        assert result["collage"] is False
        assert result["sprite_mode"] is False
        assert result["quality"] == "high"
    
    def test_anti_collage_enforcement_rejects_collage(self):
        """Test that enabling collage raises an error."""
        service = NanoBananaService()
        
        # Test that trying to enable collage raises ValueError
        params = {"collage": True}
        with pytest.raises(ValueError, match="Collage mode cannot be enabled"):
            service._enforce_anti_collage_parameters(params)
    
    def test_anti_collage_enforcement_rejects_sprite(self):
        """Test that enabling sprite_mode raises an error."""
        service = NanoBananaService()
        
        # Test that trying to enable sprite_mode raises ValueError
        params = {"sprite_mode": True}
        with pytest.raises(ValueError, match="Sprite mode cannot be enabled"):
            service._enforce_anti_collage_parameters(params)
    
    def test_identity_strength_validation_passes(self):
        """Test identity strength validation with valid strength."""
        service = NanoBananaService()
        
        # Should not raise for identity strength >= 0.95
        service._validate_identity_strength(0.95, "test_face_id")
        service._validate_identity_strength(0.97, "test_face_id")
        service._validate_identity_strength(1.0, "test_face_id")
    
    def test_identity_strength_validation_fails(self):
        """Test identity strength validation with invalid strength."""
        from app.services.nano_banana_service import IdentityConsistencyError
        
        service = NanoBananaService()
        
        # Should raise for identity strength < 0.95
        with pytest.raises(IdentityConsistencyError, match="Identity strength"):
            service._validate_identity_strength(0.94, "test_face_id")
        
        with pytest.raises(IdentityConsistencyError, match="face drift"):
            service._validate_identity_strength(0.80, "test_face_id")
    
    def test_single_scene_validation_passes(self):
        """Test single scene validation with valid output."""
        service = NanoBananaService()
        
        # Valid response with single image
        response_data = {
            "images": [
                {
                    "url": "https://example.com/image.jpg",
                    "is_collage": False,
                    "is_sprite": False
                }
            ]
        }
        
        # Should not raise
        service._validate_single_scene_output(response_data)
    
    def test_single_scene_validation_fails_no_images(self):
        """Test single scene validation fails with no images."""
        from app.services.nano_banana_service import FormatComplianceError
        
        service = NanoBananaService()
        
        response_data = {"images": []}
        
        with pytest.raises(FormatComplianceError, match="No images"):
            service._validate_single_scene_output(response_data)
    
    def test_single_scene_validation_fails_multiple_images(self):
        """Test single scene validation fails with multiple images."""
        from app.services.nano_banana_service import FormatComplianceError
        
        service = NanoBananaService()
        
        response_data = {
            "images": [
                {"url": "image1.jpg", "is_collage": False, "is_sprite": False},
                {"url": "image2.jpg", "is_collage": False, "is_sprite": False}
            ]
        }
        
        with pytest.raises(FormatComplianceError, match="Expected exactly 1"):
            service._validate_single_scene_output(response_data)
    
    def test_single_scene_validation_fails_collage_flag(self):
        """Test single scene validation fails when collage flag is set."""
        from app.services.nano_banana_service import FormatComplianceError
        
        service = NanoBananaService()
        
        response_data = {
            "images": [
                {"url": "image.jpg", "is_collage": True, "is_sprite": False}
            ]
        }
        
        with pytest.raises(FormatComplianceError, match="marked as collage"):
            service._validate_single_scene_output(response_data)


class TestFormatComplianceService:
    """Tests for format compliance service."""
    
    def test_get_format_config_reel(self):
        """Test getting format config for Reels."""
        config = FormatComplianceService.get_format_config("reel_9_16")
        
        assert config.aspect_ratio == "9:16"
        assert config.width == 1080
        assert config.height == 1920
        assert config.format_name == "Instagram Reel"
    
    def test_get_format_config_feed(self):
        """Test getting format config for Feed."""
        config = FormatComplianceService.get_format_config("feed_4_5")
        
        assert config.aspect_ratio == "4:5"
        assert config.width == 1080
        assert config.height == 1350
        assert config.format_name == "Instagram Feed"
    
    def test_get_format_config_square(self):
        """Test getting format config for Square."""
        config = FormatComplianceService.get_format_config("square_1_1")
        
        assert config.aspect_ratio == "1:1"
        assert config.width == 1080
        assert config.height == 1080
        assert config.format_name == "Instagram Square"
    
    def test_get_format_config_invalid(self):
        """Test getting format config with invalid format."""
        with pytest.raises(ValueError, match="Invalid format type"):
            FormatComplianceService.get_format_config("invalid_format")
    
    def test_calculate_aspect_ratio(self):
        """Test aspect ratio calculation."""
        # 9:16 ratio
        ratio = FormatComplianceService.calculate_aspect_ratio(1080, 1920)
        assert abs(ratio - 0.5625) < 0.001
        
        # 4:5 ratio
        ratio = FormatComplianceService.calculate_aspect_ratio(1080, 1350)
        assert abs(ratio - 0.8) < 0.001
        
        # 1:1 ratio
        ratio = FormatComplianceService.calculate_aspect_ratio(1080, 1080)
        assert ratio == 1.0
    
    def test_validate_aspect_ratio_reel_valid(self):
        """Test aspect ratio validation for valid Reel dimensions."""
        is_valid, error = FormatComplianceService.validate_aspect_ratio(
            1080, 1920, "reel_9_16"
        )
        
        assert is_valid is True
        assert error == ""
    
    def test_validate_aspect_ratio_reel_invalid(self):
        """Test aspect ratio validation for invalid Reel dimensions."""
        is_valid, error = FormatComplianceService.validate_aspect_ratio(
            1080, 1080, "reel_9_16"
        )
        
        assert is_valid is False
        assert "Aspect ratio mismatch" in error
    
    def test_validate_aspect_ratio_feed_valid(self):
        """Test aspect ratio validation for valid Feed dimensions."""
        is_valid, error = FormatComplianceService.validate_aspect_ratio(
            1080, 1350, "feed_4_5"
        )
        
        assert is_valid is True
        assert error == ""
    
    def test_validate_aspect_ratio_square_valid(self):
        """Test aspect ratio validation for valid Square dimensions."""
        is_valid, error = FormatComplianceService.validate_aspect_ratio(
            1080, 1080, "square_1_1"
        )
        
        assert is_valid is True
        assert error == ""
    
    def test_validate_resolution_4k(self):
        """Test resolution validation for 4K."""
        is_valid, errors, warnings = FormatComplianceService.validate_resolution(
            3840, 2160, require_4k=True
        )
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_resolution_below_4k(self):
        """Test resolution validation below 4K."""
        is_valid, errors, warnings = FormatComplianceService.validate_resolution(
            1080, 1920, require_4k=True
        )
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("4K" in error for error in errors)
    
    def test_validate_resolution_instagram_minimum(self):
        """Test resolution validation at Instagram minimum."""
        is_valid, errors, warnings = FormatComplianceService.validate_resolution(
            1080, 1350, require_4k=False
        )
        
        assert is_valid is True
        assert len(errors) == 0
    
    def test_validate_resolution_below_instagram_minimum(self):
        """Test resolution validation below Instagram minimum."""
        is_valid, errors, warnings = FormatComplianceService.validate_resolution(
            800, 1000, require_4k=False
        )
        
        assert is_valid is False
        assert len(errors) > 0
        assert any("Instagram minimum" in error for error in errors)
    
    def test_get_format_parameters_for_generation(self):
        """Test getting format parameters for generation API."""
        params = FormatComplianceService.get_format_parameters_for_generation("reel_9_16")
        
        assert params["aspect_ratio"] == "9:16"
        assert params["width"] == 1080
        assert params["height"] == 1920
        assert params["target_resolution"] == "4k"
        assert params["maintain_aspect_ratio"] is True
    
    def test_get_all_supported_formats(self):
        """Test getting all supported formats."""
        formats = FormatComplianceService.get_all_supported_formats()
        
        assert len(formats) == 3
        format_types = [f["format_type"] for f in formats]
        assert "reel_9_16" in format_types
        assert "feed_4_5" in format_types
        assert "square_1_1" in format_types
    
    def test_validate_format_compliance_with_valid_image(self):
        """Test format compliance validation with a valid image."""
        # Create a test image with correct dimensions for Feed format
        img = Image.new('RGB', (1080, 1350), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        result = FormatComplianceService.validate_format_compliance(
            img_bytes.getvalue(),
            "feed_4_5",
            require_4k=False  # Don't require 4K for this test
        )
        
        assert result.is_valid is True
        assert result.format_type == "feed_4_5"
        assert result.actual_width == 1080
        assert result.actual_height == 1350
        assert result.resolution_compliant is True
    
    def test_validate_format_compliance_with_wrong_aspect_ratio(self):
        """Test format compliance validation with wrong aspect ratio."""
        # Create a test image with wrong dimensions for Feed format
        img = Image.new('RGB', (1080, 1080), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        
        result = FormatComplianceService.validate_format_compliance(
            img_bytes.getvalue(),
            "feed_4_5",
            require_4k=False
        )
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        assert any("Aspect ratio mismatch" in error for error in result.errors)
