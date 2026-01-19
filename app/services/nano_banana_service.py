"""
Nano Banana API client service for image generation.

This service handles integration with Google's Nano Banana (Gemini 2.5 Flash Image) API
with focus on identity consistency, anti-collage enforcement, and retry logic.

Requirements covered:
- 3.4: Identity consistency validation (identity strength >= 0.95)
- 3.5: No face drift across generations
- 8.1: Anti-collage enforcement (collage=false)
- 8.2: Anti-sprite enforcement (sprite_mode=false)
- 8.4: Multiple variations as separate files
- 8.5: Single complete scene validation
"""
import logging
import time
from typing import Optional, Dict, Any, Tuple
from enum import Enum
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    before_sleep_log
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class NanoBananaError(Exception):
    """Base exception for Nano Banana API errors."""
    pass


class IdentityConsistencyError(NanoBananaError):
    """Exception raised when identity consistency validation fails."""
    pass


class FormatComplianceError(NanoBananaError):
    """Exception raised when format compliance validation fails."""
    pass


class APIConnectionError(NanoBananaError):
    """Exception raised for API connection issues (retryable)."""
    pass


class NanoBananaService:
    """
    Service for interacting with Nano Banana API.
    
    Implements:
    - Retry logic with exponential backoff (3 attempts max)
    - Identity consistency validation (>= 0.95)
    - Anti-collage parameter enforcement
    - Format compliance checking
    """
    
    # API Configuration
    API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
    API_TIMEOUT = 120  # 2 minutes for image generation
    
    # Identity consistency threshold (Requirement 3.4)
    MIN_IDENTITY_STRENGTH = 0.95
    
    # Anti-collage enforcement (Requirements 8.1, 8.2)
    REQUIRED_PARAMETERS = {
        "collage": False,
        "sprite_mode": False
    }
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Nano Banana service.
        
        Args:
            api_key: Optional API key override (defaults to settings)
        """
        self.api_key = api_key or settings.NANO_BANANA_API_KEY
        self.client = httpx.AsyncClient(
            timeout=self.API_TIMEOUT,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
        )
    
    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()
    
    def _enforce_anti_collage_parameters(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enforce anti-collage parameters in generation request.
        
        Requirements 8.1, 8.2: Ensure collage and sprite_mode are disabled.
        
        Args:
            parameters: Generation parameters
            
        Returns:
            Parameters with anti-collage enforcement applied
            
        Raises:
            ValueError: If parameters explicitly enable collage/sprite_mode
        """
        # Check if user is trying to enable collage/sprite_mode
        if parameters.get("collage", False) is not False:
            raise ValueError(
                "Collage mode cannot be enabled. System enforces single-scene generation."
            )
        
        if parameters.get("sprite_mode", False) is not False:
            raise ValueError(
                "Sprite mode cannot be enabled. System enforces single-scene generation."
            )
        
        # Force anti-collage parameters
        parameters["collage"] = False
        parameters["sprite_mode"] = False
        
        logger.info("Anti-collage parameters enforced: collage=False, sprite_mode=False")
        
        return parameters
    
    def _validate_identity_strength(
        self,
        identity_strength: float,
        face_id: str
    ) -> None:
        """
        Validate identity consistency meets minimum threshold.
        
        Requirement 3.4: Identity strength must be >= 0.95
        Requirement 3.5: Prevent face drift
        
        Args:
            identity_strength: Calculated identity strength score
            face_id: Face ID for logging
            
        Raises:
            IdentityConsistencyError: If identity strength is below threshold
        """
        if identity_strength < self.MIN_IDENTITY_STRENGTH:
            error_msg = (
                f"Identity strength {identity_strength:.3f} is below minimum "
                f"{self.MIN_IDENTITY_STRENGTH} for face {face_id}. "
                f"This indicates potential face drift."
            )
            logger.error(error_msg)
            raise IdentityConsistencyError(error_msg)
        
        logger.info(
            f"Identity validation passed: {identity_strength:.3f} >= "
            f"{self.MIN_IDENTITY_STRENGTH} for face {face_id}"
        )
    
    def _validate_single_scene_output(self, response_data: Dict[str, Any]) -> None:
        """
        Validate that output contains exactly one complete scene.
        
        Requirement 8.5: Validate output contains exactly one complete scene
        
        Args:
            response_data: API response data
            
        Raises:
            FormatComplianceError: If output is not a single scene
        """
        # Check if response contains multiple images (collage/sprite)
        images = response_data.get("images", [])
        
        if len(images) == 0:
            raise FormatComplianceError("No images in generation output")
        
        if len(images) > 1:
            raise FormatComplianceError(
                f"Output contains {len(images)} images. Expected exactly 1 complete scene. "
                f"This may indicate collage or sprite mode was not properly disabled."
            )
        
        # Validate image metadata indicates single scene
        image_data = images[0]
        if image_data.get("is_collage", False):
            raise FormatComplianceError("Output is marked as collage despite enforcement")
        
        if image_data.get("is_sprite", False):
            raise FormatComplianceError("Output is marked as sprite despite enforcement")
        
        logger.info("Single scene validation passed: exactly 1 complete image")
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=2, min=2, max=10),
        retry=retry_if_exception_type(APIConnectionError),
        before_sleep=before_sleep_log(logger, logging.WARNING)
    )
    async def generate_image(
        self,
        prompt: str,
        face_embedding: bytes,
        face_id: str,
        style_parameters: Dict[str, Any],
        format_config: Dict[str, Any]
    ) -> Tuple[str, float, Dict[str, Any]]:
        """
        Generate image using Nano Banana API with identity consistency.
        
        This method implements:
        - Automatic retry with exponential backoff (3 attempts)
        - Anti-collage parameter enforcement
        - Identity consistency validation
        - Single scene output validation
        
        Args:
            prompt: Generation prompt (from preset)
            face_embedding: Encrypted face embedding data
            face_id: Face ID for tracking
            style_parameters: Style parameters from preset
            format_config: Format configuration (aspect ratio, resolution)
            
        Returns:
            Tuple of (image_url, identity_strength, metadata)
            
        Raises:
            IdentityConsistencyError: If identity strength < 0.95
            FormatComplianceError: If output is not single scene
            APIConnectionError: For retryable API errors
            NanoBananaError: For non-retryable errors
        """
        # Demo mode for testing without real API
        if settings.DEMO_MODE:
            logger.warning("DEMO MODE: Returning fake image generation result")
            return await self._generate_demo_image(prompt, face_id, style_parameters, format_config)
        
        start_time = time.time()
        
        try:
            # Enforce anti-collage parameters
            style_parameters = self._enforce_anti_collage_parameters(style_parameters.copy())
            
            # Build request payload
            payload = {
                "prompt": prompt,
                "face_embedding": face_embedding.hex(),  # Convert bytes to hex string
                "style_parameters": style_parameters,
                "format_config": format_config,
                "identity_strength_threshold": self.MIN_IDENTITY_STRENGTH
            }
            
            logger.info(
                f"Generating image for face {face_id} with prompt: {prompt[:100]}..."
            )
            
            # Make API request
            response = await self.client.post(
                f"{self.API_BASE_URL}/models/gemini-2.5-flash-image:generate",
                json=payload
            )
            
            # Handle API errors
            if response.status_code == 429:
                # Rate limit - retryable
                raise APIConnectionError("Rate limit exceeded")
            elif response.status_code >= 500:
                # Server error - retryable
                raise APIConnectionError(f"Server error: {response.status_code}")
            elif response.status_code == 401:
                # Auth error - not retryable
                raise NanoBananaError("Invalid API key")
            elif response.status_code >= 400:
                # Client error - not retryable
                error_data = response.json()
                raise NanoBananaError(
                    f"API error: {error_data.get('error', {}).get('message', 'Unknown error')}"
                )
            
            response.raise_for_status()
            response_data = response.json()
            
            # Extract results
            image_url = response_data.get("image_url")
            identity_strength = response_data.get("identity_strength", 0.0)
            metadata = response_data.get("metadata", {})
            
            if not image_url:
                raise NanoBananaError("No image URL in API response")
            
            # Validate identity consistency (Requirement 3.4, 3.5)
            self._validate_identity_strength(identity_strength, face_id)
            
            # Validate single scene output (Requirement 8.5)
            self._validate_single_scene_output(response_data)
            
            processing_time = time.time() - start_time
            logger.info(
                f"Image generation successful for face {face_id}. "
                f"Identity strength: {identity_strength:.3f}, "
                f"Processing time: {processing_time:.2f}s"
            )
            
            # Add processing metadata
            metadata.update({
                "processing_time_seconds": processing_time,
                "identity_strength": identity_strength,
                "face_id": face_id,
                "anti_collage_enforced": True
            })
            
            return image_url, identity_strength, metadata
            
        except (IdentityConsistencyError, FormatComplianceError):
            # Re-raise validation errors (not retryable)
            raise
        except httpx.TimeoutException as e:
            # Timeout - retryable
            logger.warning(f"API timeout for face {face_id}: {e}")
            raise APIConnectionError(f"API timeout: {e}")
        except httpx.NetworkError as e:
            # Network error - retryable
            logger.warning(f"Network error for face {face_id}: {e}")
            raise APIConnectionError(f"Network error: {e}")
        except Exception as e:
            # Unexpected error
            logger.error(f"Unexpected error in image generation: {e}", exc_info=True)
            raise NanoBananaError(f"Unexpected error: {e}")
    
    async def _generate_demo_image(
        self,
        prompt: str,
        face_id: str,
        style_parameters: Dict[str, Any],
        format_config: Dict[str, Any]
    ) -> Tuple[str, float, Dict[str, Any]]:
        """
        Generate a demo/fake image for testing without real API.
        
        Returns placeholder data that passes all validations.
        """
        import asyncio
        
        # Simulate API delay
        await asyncio.sleep(2)
        
        # Return fake but valid data
        demo_image_url = "https://via.placeholder.com/1080x1350/FF6B6B/FFFFFF?text=Demo+Image"
        identity_strength = 0.98  # Above threshold
        metadata = {
            "processing_time_seconds": 2.0,
            "identity_strength": identity_strength,
            "face_id": face_id,
            "anti_collage_enforced": True,
            "demo_mode": True,
            "prompt": prompt[:100],
            "format_config": format_config
        }
        
        logger.info(
            f"Demo image generated for face {face_id}. "
            f"Identity strength: {identity_strength:.3f}"
        )
        
        return demo_image_url, identity_strength, metadata
    
    async def validate_face_embedding(
        self,
        face_embedding: bytes,
        reference_image_url: str
    ) -> Tuple[bool, float, Optional[str]]:
        """
        Validate face embedding quality and identity strength.
        
        Args:
            face_embedding: Face embedding data to validate
            reference_image_url: URL of reference face image
            
        Returns:
            Tuple of (is_valid, identity_strength, error_message)
        """
        try:
            payload = {
                "face_embedding": face_embedding.hex(),
                "reference_image_url": reference_image_url
            }
            
            response = await self.client.post(
                f"{self.API_BASE_URL}/models/gemini-2.5-flash-image:validate-embedding",
                json=payload
            )
            
            if response.status_code != 200:
                return False, 0.0, f"Validation failed: {response.status_code}"
            
            data = response.json()
            identity_strength = data.get("identity_strength", 0.0)
            is_valid = identity_strength >= self.MIN_IDENTITY_STRENGTH
            
            error_message = None if is_valid else (
                f"Identity strength {identity_strength:.3f} below threshold "
                f"{self.MIN_IDENTITY_STRENGTH}"
            )
            
            return is_valid, identity_strength, error_message
            
        except Exception as e:
            logger.error(f"Error validating face embedding: {e}")
            return False, 0.0, str(e)
    
    def get_format_parameters(self, format_type: str) -> Dict[str, Any]:
        """
        Get format parameters for Instagram format types.
        
        Uses the format compliance system to get validated parameters.
        
        Args:
            format_type: Format type (reel_9_16, feed_4_5, square_1_1)
            
        Returns:
            Dictionary of format parameters
        """
        from app.services.format_compliance_service import FormatComplianceService
        
        return FormatComplianceService.get_format_parameters_for_generation(format_type)
