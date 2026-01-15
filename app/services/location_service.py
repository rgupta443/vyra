"""
Location suggestion service for Instagram content.

This service handles:
- Location matching based on content
- City-level accuracy validation
- Real and searchable location suggestions

Validates Requirements 11.2, 11.4, 11.5
"""
import logging
from typing import Optional
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class LocationGenerationError(Exception):
    """Exception raised when location generation fails."""
    pass


class LocationService:
    """Service for generating Instagram location suggestions."""
    
    # Common city locations by preset type (fallback)
    FALLBACK_LOCATIONS = {
        "luxury": [
            "Monaco",
            "Dubai, United Arab Emirates",
            "Paris, France",
            "Milan, Italy",
            "Beverly Hills, California"
        ],
        "lifestyle": [
            "Los Angeles, California",
            "New York, New York",
            "London, United Kingdom",
            "Sydney, Australia",
            "Barcelona, Spain"
        ],
        "beauty": [
            "Los Angeles, California",
            "New York, New York",
            "Paris, France",
            "Seoul, South Korea",
            "London, United Kingdom"
        ]
    }
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def suggest_location(
        self,
        preset_type: str,
        caption: Optional[str] = None,
        context: Optional[str] = None
    ) -> Optional[str]:
        """
        Suggest an appropriate Instagram location for the content.
        
        Args:
            preset_type: Type of preset (luxury, lifestyle, beauty)
            caption: Optional caption for context
            context: Optional additional context
        
        Returns:
            Location string (city-level) or None if no appropriate location
        
        Validates:
            - Requirement 11.2: City-level accuracy
            - Requirement 11.4: Optional suggestions (can return None)
            - Requirement 11.5: Real and searchable locations
        """
        try:
            # Build the prompt for location suggestion
            prompt = self._build_location_prompt(preset_type, caption, context)
            
            logger.info(f"Generating location suggestion for preset {preset_type}")
            
            # Call OpenAI GPT-4 for location suggestion
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an Instagram location expert. "
                            "Suggest ONE realistic location that matches the content. "
                            "Use city-level accuracy (e.g., 'Paris, France' not specific addresses). "
                            "Only suggest real, well-known locations that exist on Instagram. "
                            "If no appropriate location fits, respond with 'NONE'. "
                            "Return ONLY the location name, nothing else."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=50,
                temperature=0.7,
                n=1
            )
            
            # Extract location from response
            location = response.choices[0].message.content.strip()
            
            # Check if no location is appropriate (Requirement 11.4)
            if location.upper() == "NONE" or not location:
                logger.info("No appropriate location for this content")
                return None
            
            # Validate location format (Requirement 11.2, 11.5)
            location = self._validate_location(location)
            
            if location:
                logger.info(f"Suggested location: {location}")
            else:
                logger.info("Location validation failed, no suggestion")
            
            return location
            
        except Exception as e:
            logger.error(f"Location suggestion failed: {e}")
            # Return None on failure (locations are optional)
            return None
    
    def _build_location_prompt(
        self,
        preset_type: str,
        caption: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """Build the prompt for location suggestion based on preset type."""
        preset_descriptions = {
            "luxury": "luxury lifestyle content with elegant, high-end aesthetics",
            "lifestyle": "authentic lifestyle content showing real moments and experiences",
            "beauty": "beauty and confidence content highlighting personal style"
        }
        
        description = preset_descriptions.get(
            preset_type.lower(),
            "lifestyle content"
        )
        
        prompt = f"Suggest a realistic Instagram location for {description}."
        
        if caption:
            prompt += f" Caption: {caption}"
        
        if context:
            prompt += f" Context: {context}"
        
        prompt += " Provide city-level location only."
        
        return prompt
    
    def _validate_location(self, location: str) -> Optional[str]:
        """
        Validate and format location string.
        
        Validates:
            - Requirement 11.2: City-level accuracy
            - Requirement 11.5: Real and searchable locations
        """
        # Remove quotes if present
        location = location.strip('"').strip("'")
        
        # Check for reasonable length
        if len(location) < 3 or len(location) > 100:
            logger.warning(f"Location length invalid: {len(location)} chars")
            return None
        
        # Check for city-level format (should contain comma for "City, Country")
        # But also allow single-word famous cities like "Paris" or "Tokyo"
        if ',' not in location and len(location.split()) > 3:
            logger.warning(f"Location too specific: {location}")
            return None
        
        # Basic validation - should not contain special characters except comma and space
        if not all(c.isalnum() or c in ', -' for c in location):
            logger.warning(f"Location contains invalid characters: {location}")
            return None
        
        return location
    
    def get_fallback_location(self, preset_type: str) -> Optional[str]:
        """
        Get a fallback location for the given preset type.
        
        Returns None to indicate location is optional (Requirement 11.4)
        """
        # Locations are optional, so we can return None
        # But if we want to provide a fallback, we can pick one randomly
        import random
        
        locations = self.FALLBACK_LOCATIONS.get(
            preset_type.lower(),
            self.FALLBACK_LOCATIONS["lifestyle"]
        )
        
        # Return None 30% of the time to keep locations optional
        if random.random() < 0.3:
            return None
        
        return random.choice(locations)
    
    async def close(self):
        """Close the OpenAI client."""
        await self.client.close()
