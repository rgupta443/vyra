"""
Caption generation service using OpenAI GPT-4.

This service handles:
- Caption generation with length validation (1-2 lines)
- Fallback caption system for failures
- Natural human tone without excessive emoji usage

Validates Requirements 9.1, 9.2, 9.5
"""
import logging
from typing import Optional, Tuple
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class CaptionGenerationError(Exception):
    """Exception raised when caption generation fails."""
    pass


class CaptionService:
    """Service for generating Instagram captions using OpenAI GPT-4."""
    
    # Fallback captions by preset type (Requirement 9.5)
    FALLBACK_CAPTIONS = {
        "luxury": "Living my best life ✨",
        "lifestyle": "Making memories that matter 🌟",
        "beauty": "Confidence is the best accessory 💫"
    }
    
    # Maximum caption length in characters (approximately 1-2 lines)
    MAX_CAPTION_LENGTH = 150
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_caption(
        self,
        preset_type: str,
        image_url: Optional[str] = None,
        context: Optional[str] = None
    ) -> Tuple[str, bool]:
        """
        Generate an Instagram caption for the given preset and image.
        
        Args:
            preset_type: Type of preset (luxury, lifestyle, beauty)
            image_url: Optional URL of the generated image for context
            context: Optional additional context for caption generation
        
        Returns:
            Tuple of (caption, is_fallback)
            - caption: Generated or fallback caption
            - is_fallback: True if fallback was used, False if generated
        
        Validates:
            - Requirement 9.1: Automatic caption generation
            - Requirement 9.2: 1-2 line length limit
            - Requirement 9.5: Fallback caption on failure
        """
        try:
            # Build the prompt for caption generation
            prompt = self._build_caption_prompt(preset_type, context)
            
            logger.info(f"Generating caption for preset {preset_type}")
            
            # Call OpenAI GPT-4 for caption generation
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an expert Instagram caption writer. "
                            "Generate engaging, natural captions that sound human. "
                            "Keep captions to 1-2 lines maximum (under 150 characters). "
                            "Use minimal emojis (0-2 max). "
                            "Match the tone to the content style. "
                            "Be authentic and relatable."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=100,
                temperature=0.8,
                n=1
            )
            
            # Extract caption from response
            caption = response.choices[0].message.content.strip()
            
            # Validate caption length (Requirement 9.2)
            if len(caption) > self.MAX_CAPTION_LENGTH:
                logger.warning(
                    f"Generated caption too long ({len(caption)} chars), truncating"
                )
                caption = self._truncate_caption(caption)
            
            # Remove quotes if present
            caption = caption.strip('"').strip("'")
            
            logger.info(f"Successfully generated caption: {caption[:50]}...")
            return caption, False
            
        except Exception as e:
            logger.error(f"Caption generation failed: {e}")
            # Return fallback caption (Requirement 9.5)
            fallback = self._get_fallback_caption(preset_type)
            logger.info(f"Using fallback caption: {fallback}")
            return fallback, True
    
    def _build_caption_prompt(self, preset_type: str, context: Optional[str] = None) -> str:
        """Build the prompt for caption generation based on preset type."""
        preset_descriptions = {
            "luxury": (
                "high-end luxury lifestyle content featuring elegant settings, "
                "sophisticated aesthetics, and premium experiences"
            ),
            "lifestyle": (
                "authentic lifestyle content showing real moments, "
                "personal experiences, and everyday adventures"
            ),
            "beauty": (
                "beauty and confidence content highlighting natural beauty, "
                "self-care, and personal style"
            )
        }
        
        description = preset_descriptions.get(
            preset_type.lower(),
            "lifestyle content"
        )
        
        prompt = f"Write a short Instagram caption (1-2 lines) for {description}."
        
        if context:
            prompt += f" Context: {context}"
        
        prompt += " Make it engaging and authentic."
        
        return prompt
    
    def _truncate_caption(self, caption: str) -> str:
        """
        Truncate caption to maximum length while preserving word boundaries.
        
        Validates Requirement 9.2: Caption length limit
        """
        if len(caption) <= self.MAX_CAPTION_LENGTH:
            return caption
        
        # Truncate at word boundary
        truncated = caption[:self.MAX_CAPTION_LENGTH].rsplit(' ', 1)[0]
        
        # Add ellipsis if truncated
        if truncated != caption:
            truncated += "..."
        
        return truncated
    
    def _get_fallback_caption(self, preset_type: str) -> str:
        """
        Get fallback caption for the given preset type.
        
        Validates Requirement 9.5: Fallback caption system
        """
        return self.FALLBACK_CAPTIONS.get(
            preset_type.lower(),
            self.FALLBACK_CAPTIONS["lifestyle"]
        )
    
    async def close(self):
        """Close the OpenAI client."""
        await self.client.close()
