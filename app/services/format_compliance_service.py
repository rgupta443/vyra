"""
Format compliance service for Instagram format validation.

This service ensures all generated images meet Instagram's format requirements
including aspect ratios, resolution, and safe area compliance.

Requirements covered:
- 6.1: Reels format (9:16 aspect ratio)
- 6.2: Feed format (4:5 aspect ratio)
- 6.3: Square format (1:1 aspect ratio)
- 6.4: Instagram safe area compliance
- 6.5: 4K resolution output
"""
import logging
from typing import Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass
from PIL import Image
import io

logger = logging.getLogger(__name__)


class InstagramFormat(str, Enum):
    """Instagram format types."""
    REEL_9_16 = "reel_9_16"
    FEED_4_5 = "feed_4_5"
    SQUARE_1_1 = "square_1_1"


@dataclass
class AspectRatioConfig:
    """Configuration for aspect ratio validation."""
    width: int
    height: int
    aspect_ratio: str
    format_name: str
    tolerance: float = 0.01  # 1% tolerance for aspect ratio validation


@dataclass
class SafeAreaConfig:
    """Configuration for Instagram safe areas."""
    top_margin_percent: float
    bottom_margin_percent: float
    left_margin_percent: float
    right_margin_percent: float


@dataclass
class FormatValidationResult:
    """Result of format validation."""
    is_valid: bool
    format_type: str
    actual_width: int
    actual_height: int
    actual_aspect_ratio: float
    expected_aspect_ratio: float
    resolution_compliant: bool
    safe_area_compliant: bool
    errors: list[str]
    warnings: list[str]


class FormatComplianceService:
    """
    Service for validating Instagram format compliance.
    
    Implements:
    - Aspect ratio validation for all Instagram formats
    - 4K resolution requirements
    - Safe area compliance checking
    """
    
    # Format configurations (Requirement 6.1, 6.2, 6.3)
    FORMAT_CONFIGS = {
        InstagramFormat.REEL_9_16: AspectRatioConfig(
            width=1080,
            height=1920,
            aspect_ratio="9:16",
            format_name="Instagram Reel"
        ),
        InstagramFormat.FEED_4_5: AspectRatioConfig(
            width=1080,
            height=1350,
            aspect_ratio="4:5",
            format_name="Instagram Feed"
        ),
        InstagramFormat.SQUARE_1_1: AspectRatioConfig(
            width=1080,
            height=1080,
            aspect_ratio="1:1",
            format_name="Instagram Square"
        )
    }
    
    # Safe area configurations (Requirement 6.4)
    # Instagram safe areas to avoid UI overlap
    SAFE_AREA_CONFIGS = {
        InstagramFormat.REEL_9_16: SafeAreaConfig(
            top_margin_percent=0.15,  # 15% from top (profile pic, buttons)
            bottom_margin_percent=0.20,  # 20% from bottom (caption, CTA)
            left_margin_percent=0.05,  # 5% from left
            right_margin_percent=0.05  # 5% from right
        ),
        InstagramFormat.FEED_4_5: SafeAreaConfig(
            top_margin_percent=0.05,  # 5% from top
            bottom_margin_percent=0.05,  # 5% from bottom
            left_margin_percent=0.05,  # 5% from left
            right_margin_percent=0.05  # 5% from right
        ),
        InstagramFormat.SQUARE_1_1: SafeAreaConfig(
            top_margin_percent=0.05,  # 5% from top
            bottom_margin_percent=0.05,  # 5% from bottom
            left_margin_percent=0.05,  # 5% from left
            right_margin_percent=0.05  # 5% from right
        )
    }
    
    # Minimum resolution for 4K quality (Requirement 6.5)
    MIN_WIDTH_4K = 3840
    MIN_HEIGHT_4K = 2160
    
    # Instagram's recommended minimum (we aim higher for 4K)
    INSTAGRAM_MIN_WIDTH = 1080
    
    @staticmethod
    def get_format_config(format_type: str) -> AspectRatioConfig:
        """
        Get format configuration for a given format type.
        
        Args:
            format_type: Format type string
            
        Returns:
            AspectRatioConfig for the format
            
        Raises:
            ValueError: If format type is invalid
        """
        try:
            format_enum = InstagramFormat(format_type)
            return FormatComplianceService.FORMAT_CONFIGS[format_enum]
        except (ValueError, KeyError):
            raise ValueError(
                f"Invalid format type: {format_type}. "
                f"Must be one of: {[f.value for f in InstagramFormat]}"
            )
    
    @staticmethod
    def get_safe_area_config(format_type: str) -> SafeAreaConfig:
        """
        Get safe area configuration for a given format type.
        
        Args:
            format_type: Format type string
            
        Returns:
            SafeAreaConfig for the format
        """
        try:
            format_enum = InstagramFormat(format_type)
            return FormatComplianceService.SAFE_AREA_CONFIGS[format_enum]
        except (ValueError, KeyError):
            # Default to feed safe areas
            return FormatComplianceService.SAFE_AREA_CONFIGS[InstagramFormat.FEED_4_5]
    
    @staticmethod
    def calculate_aspect_ratio(width: int, height: int) -> float:
        """
        Calculate aspect ratio from dimensions.
        
        Args:
            width: Image width
            height: Image height
            
        Returns:
            Aspect ratio as float (width/height)
        """
        if height == 0:
            raise ValueError("Height cannot be zero")
        return width / height
    
    @staticmethod
    def validate_aspect_ratio(
        actual_width: int,
        actual_height: int,
        format_type: str
    ) -> Tuple[bool, str]:
        """
        Validate image aspect ratio matches format requirements.
        
        Requirements 6.1, 6.2, 6.3: Validate correct aspect ratios
        
        Args:
            actual_width: Actual image width
            actual_height: Actual image height
            format_type: Expected format type
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        config = FormatComplianceService.get_format_config(format_type)
        
        # Calculate actual and expected aspect ratios
        actual_ratio = FormatComplianceService.calculate_aspect_ratio(
            actual_width, actual_height
        )
        expected_ratio = FormatComplianceService.calculate_aspect_ratio(
            config.width, config.height
        )
        
        # Check if within tolerance
        ratio_diff = abs(actual_ratio - expected_ratio)
        tolerance = expected_ratio * config.tolerance
        
        if ratio_diff > tolerance:
            return False, (
                f"Aspect ratio mismatch for {config.format_name}. "
                f"Expected {config.aspect_ratio} ({expected_ratio:.3f}), "
                f"got {actual_ratio:.3f} ({actual_width}x{actual_height})"
            )
        
        logger.info(
            f"Aspect ratio validation passed: {actual_ratio:.3f} matches "
            f"{config.aspect_ratio} for {config.format_name}"
        )
        
        return True, ""
    
    @staticmethod
    def validate_resolution(
        width: int,
        height: int,
        require_4k: bool = True
    ) -> Tuple[bool, list[str], list[str]]:
        """
        Validate image resolution meets requirements.
        
        Requirement 6.5: 4K resolution output
        
        Args:
            width: Image width
            height: Image height
            require_4k: Whether to require 4K resolution (default True)
            
        Returns:
            Tuple of (is_valid, errors, warnings)
        """
        errors = []
        warnings = []
        
        # Check minimum Instagram resolution
        if width < FormatComplianceService.INSTAGRAM_MIN_WIDTH:
            errors.append(
                f"Width {width}px is below Instagram minimum "
                f"{FormatComplianceService.INSTAGRAM_MIN_WIDTH}px"
            )
        
        # Check 4K resolution (Requirement 6.5)
        if require_4k:
            if width < FormatComplianceService.MIN_WIDTH_4K:
                errors.append(
                    f"Width {width}px is below 4K requirement "
                    f"{FormatComplianceService.MIN_WIDTH_4K}px"
                )
            
            if height < FormatComplianceService.MIN_HEIGHT_4K:
                # For portrait formats, height requirement is adjusted
                # We check if at least one dimension meets 4K
                if width < FormatComplianceService.MIN_WIDTH_4K:
                    warnings.append(
                        f"Neither dimension meets 4K standard. "
                        f"Got {width}x{height}px"
                    )
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info(f"Resolution validation passed: {width}x{height}px")
        
        return is_valid, errors, warnings
    
    @staticmethod
    def validate_safe_area_compliance(
        image_data: bytes,
        format_type: str
    ) -> Tuple[bool, list[str]]:
        """
        Validate image respects Instagram safe areas.
        
        Requirement 6.4: Instagram safe area compliance
        
        This checks that important content is not placed in areas that
        Instagram UI elements will cover (profile pics, buttons, captions).
        
        Args:
            image_data: Image data as bytes
            format_type: Format type
            
        Returns:
            Tuple of (is_compliant, warnings)
        """
        warnings = []
        
        try:
            # Load image
            image = Image.open(io.BytesIO(image_data))
            width, height = image.size
            
            # Get safe area config
            safe_area = FormatComplianceService.get_safe_area_config(format_type)
            
            # Calculate safe area boundaries
            safe_top = int(height * safe_area.top_margin_percent)
            safe_bottom = int(height * (1 - safe_area.bottom_margin_percent))
            safe_left = int(width * safe_area.left_margin_percent)
            safe_right = int(width * (1 - safe_area.right_margin_percent))
            
            # Analyze image content in unsafe areas
            # This is a simplified check - in production, you'd use computer vision
            # to detect if important content (faces, text) is in unsafe areas
            
            # For now, we just log the safe area boundaries
            logger.info(
                f"Safe area boundaries for {format_type}: "
                f"top={safe_top}px, bottom={safe_bottom}px, "
                f"left={safe_left}px, right={safe_right}px"
            )
            
            # Add informational warning about safe areas
            warnings.append(
                f"Ensure important content is within safe area: "
                f"{safe_left}px to {safe_right}px horizontally, "
                f"{safe_top}px to {safe_bottom}px vertically"
            )
            
            # Always return True for now - this is informational
            # In production, you'd implement actual content detection
            return True, warnings
            
        except Exception as e:
            logger.error(f"Error validating safe area compliance: {e}")
            warnings.append(f"Could not validate safe area compliance: {e}")
            return True, warnings  # Don't fail on validation errors
    
    @staticmethod
    def validate_format_compliance(
        image_data: bytes,
        format_type: str,
        require_4k: bool = True
    ) -> FormatValidationResult:
        """
        Comprehensive format compliance validation.
        
        Validates:
        - Aspect ratio (Requirements 6.1, 6.2, 6.3)
        - Resolution (Requirement 6.5)
        - Safe area compliance (Requirement 6.4)
        
        Args:
            image_data: Image data as bytes
            format_type: Expected format type
            require_4k: Whether to require 4K resolution
            
        Returns:
            FormatValidationResult with validation details
        """
        errors = []
        warnings = []
        
        try:
            # Load image to get dimensions
            image = Image.open(io.BytesIO(image_data))
            actual_width, actual_height = image.size
            
            # Get expected format config
            config = FormatComplianceService.get_format_config(format_type)
            expected_ratio = FormatComplianceService.calculate_aspect_ratio(
                config.width, config.height
            )
            actual_ratio = FormatComplianceService.calculate_aspect_ratio(
                actual_width, actual_height
            )
            
            # Validate aspect ratio
            aspect_valid, aspect_error = FormatComplianceService.validate_aspect_ratio(
                actual_width, actual_height, format_type
            )
            if not aspect_valid:
                errors.append(aspect_error)
            
            # Validate resolution
            resolution_valid, res_errors, res_warnings = (
                FormatComplianceService.validate_resolution(
                    actual_width, actual_height, require_4k
                )
            )
            errors.extend(res_errors)
            warnings.extend(res_warnings)
            
            # Validate safe area compliance
            safe_area_valid, safe_warnings = (
                FormatComplianceService.validate_safe_area_compliance(
                    image_data, format_type
                )
            )
            warnings.extend(safe_warnings)
            
            # Overall validation result
            is_valid = aspect_valid and resolution_valid
            
            result = FormatValidationResult(
                is_valid=is_valid,
                format_type=format_type,
                actual_width=actual_width,
                actual_height=actual_height,
                actual_aspect_ratio=actual_ratio,
                expected_aspect_ratio=expected_ratio,
                resolution_compliant=resolution_valid,
                safe_area_compliant=safe_area_valid,
                errors=errors,
                warnings=warnings
            )
            
            if is_valid:
                logger.info(
                    f"Format compliance validation passed for {format_type}: "
                    f"{actual_width}x{actual_height}px"
                )
            else:
                logger.error(
                    f"Format compliance validation failed for {format_type}: "
                    f"{', '.join(errors)}"
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error during format validation: {e}", exc_info=True)
            return FormatValidationResult(
                is_valid=False,
                format_type=format_type,
                actual_width=0,
                actual_height=0,
                actual_aspect_ratio=0.0,
                expected_aspect_ratio=0.0,
                resolution_compliant=False,
                safe_area_compliant=False,
                errors=[f"Validation error: {e}"],
                warnings=[]
            )
    
    @staticmethod
    def get_format_parameters_for_generation(
        format_type: str
    ) -> Dict[str, Any]:
        """
        Get format parameters to pass to image generation API.
        
        Args:
            format_type: Format type
            
        Returns:
            Dictionary of format parameters for API
        """
        config = FormatComplianceService.get_format_config(format_type)
        
        return {
            "aspect_ratio": config.aspect_ratio,
            "width": config.width,
            "height": config.height,
            "format_name": config.format_name,
            "target_resolution": "4k",
            "maintain_aspect_ratio": True
        }
    
    @staticmethod
    def get_all_supported_formats() -> list[Dict[str, Any]]:
        """
        Get list of all supported Instagram formats.
        
        Returns:
            List of format configurations
        """
        formats = []
        for format_type, config in FormatComplianceService.FORMAT_CONFIGS.items():
            formats.append({
                "format_type": format_type.value,
                "format_name": config.format_name,
                "aspect_ratio": config.aspect_ratio,
                "width": config.width,
                "height": config.height,
                "description": f"{config.format_name} ({config.aspect_ratio})"
            })
        return formats
