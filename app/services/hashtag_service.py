"""
Hashtag generation and optimization service.

This service handles:
- Hashtag generation (8-12 hashtags)
- Banned hashtag filtering
- Mix of niche, brand, and reach-focused tags

Validates Requirements 10.1, 10.3, 10.5
"""
import logging
from typing import List, Set, Optional
from openai import AsyncOpenAI
from app.core.config import settings

logger = logging.getLogger(__name__)


class HashtagGenerationError(Exception):
    """Exception raised when hashtag generation fails."""
    pass


class HashtagService:
    """Service for generating and validating Instagram hashtags."""
    
    # Banned hashtags that violate Instagram policies
    # This is a subset - in production, this would be a comprehensive database
    BANNED_HASHTAGS = {
        "#porn", "#sex", "#nude", "#naked", "#nsfw",
        "#drugs", "#weed", "#cannabis",
        "#followforfollow", "#follow4follow", "#f4f", "#likeforlike", "#l4l",
        "#spam", "#bot", "#automation"
    }
    
    # Minimum and maximum hashtag counts (Requirement 10.1)
    MIN_HASHTAGS = 8
    MAX_HASHTAGS = 12
    
    def __init__(self):
        """Initialize OpenAI client."""
        self.client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    
    async def generate_hashtags(
        self,
        preset_type: str,
        caption: Optional[str] = None,
        context: Optional[str] = None
    ) -> List[str]:
        """
        Generate 8-12 relevant Instagram hashtags.
        
        Args:
            preset_type: Type of preset (luxury, lifestyle, beauty)
            caption: Optional caption for context
            context: Optional additional context
        
        Returns:
            List of 8-12 validated hashtags
        
        Validates:
            - Requirement 10.1: Generate 8-12 hashtags
            - Requirement 10.3: Filter banned hashtags
            - Requirement 10.5: Avoid spam patterns
        """
        try:
            # Build the prompt for hashtag generation
            prompt = self._build_hashtag_prompt(preset_type, caption, context)
            
            logger.info(f"Generating hashtags for preset {preset_type}")
            
            # Call OpenAI GPT-4 for hashtag generation
            response = await self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You are an Instagram hashtag expert. "
                            "Generate 10-12 relevant hashtags that mix: "
                            "1) Niche-specific tags (3-4 tags) "
                            "2) Brand/style tags (3-4 tags) "
                            "3) Reach-focused popular tags (3-4 tags). "
                            "Return ONLY hashtags, one per line, with # prefix. "
                            "Avoid banned, spam, or follow-for-follow type hashtags. "
                            "Make hashtags relevant and authentic."
                        )
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=150,
                temperature=0.7,
                n=1
            )
            
            # Extract and parse hashtags
            raw_hashtags = response.choices[0].message.content.strip()
            hashtags = self._parse_hashtags(raw_hashtags)
            
            # Filter banned hashtags (Requirement 10.3)
            hashtags = self._filter_banned_hashtags(hashtags)
            
            # Validate count (Requirement 10.1)
            hashtags = self._validate_hashtag_count(hashtags, preset_type)
            
            logger.info(f"Successfully generated {len(hashtags)} hashtags")
            return hashtags
            
        except Exception as e:
            logger.error(f"Hashtag generation failed: {e}")
            # Return fallback hashtags
            return self._get_fallback_hashtags(preset_type)
    
    def _build_hashtag_prompt(
        self,
        preset_type: str,
        caption: Optional[str] = None,
        context: Optional[str] = None
    ) -> str:
        """Build the prompt for hashtag generation based on preset type."""
        preset_descriptions = {
            "luxury": "luxury lifestyle, high-end fashion, elegant aesthetics, premium experiences",
            "lifestyle": "authentic lifestyle, personal moments, everyday adventures, real experiences",
            "beauty": "beauty, confidence, self-care, natural beauty, personal style"
        }
        
        description = preset_descriptions.get(
            preset_type.lower(),
            "lifestyle content"
        )
        
        prompt = f"Generate 10-12 Instagram hashtags for content about: {description}."
        
        if caption:
            prompt += f" Caption context: {caption}"
        
        if context:
            prompt += f" Additional context: {context}"
        
        return prompt
    
    def _parse_hashtags(self, raw_text: str) -> List[str]:
        """Parse hashtags from raw text response."""
        hashtags = []
        
        for line in raw_text.split('\n'):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            # Extract hashtag
            if line.startswith('#'):
                hashtag = line.split()[0]  # Take first word if multiple
            else:
                # Try to find hashtag in line
                words = line.split()
                hashtag = next((w for w in words if w.startswith('#')), None)
                if not hashtag:
                    continue
            
            # Clean and normalize
            hashtag = hashtag.lower().strip()
            
            # Remove any trailing punctuation
            hashtag = hashtag.rstrip('.,!?;:')
            
            # Validate format
            if self._is_valid_hashtag(hashtag):
                hashtags.append(hashtag)
        
        return hashtags
    
    def _is_valid_hashtag(self, hashtag: str) -> bool:
        """Validate hashtag format."""
        if not hashtag.startswith('#'):
            return False
        
        # Remove # for validation
        tag = hashtag[1:]
        
        # Must have content after #
        if not tag:
            return False
        
        # Must be alphanumeric (can include underscores)
        if not all(c.isalnum() or c == '_' for c in tag):
            return False
        
        # Reasonable length (Instagram limit is 30 chars per hashtag)
        if len(tag) > 30:
            return False
        
        return True
    
    def _filter_banned_hashtags(self, hashtags: List[str]) -> List[str]:
        """
        Filter out banned hashtags.
        
        Validates Requirement 10.3: Never include banned hashtags
        """
        filtered = []
        
        for hashtag in hashtags:
            hashtag_lower = hashtag.lower()
            
            # Check against banned list
            if hashtag_lower in self.BANNED_HASHTAGS:
                logger.warning(f"Filtered banned hashtag: {hashtag}")
                continue
            
            # Check for spam patterns (Requirement 10.5)
            if self._is_spam_pattern(hashtag_lower):
                logger.warning(f"Filtered spam pattern hashtag: {hashtag}")
                continue
            
            filtered.append(hashtag)
        
        return filtered
    
    def _is_spam_pattern(self, hashtag: str) -> bool:
        """
        Detect spam patterns in hashtags.
        
        Validates Requirement 10.5: Avoid spam patterns
        """
        spam_patterns = [
            'follow', 'like', 'f4f', 'l4l', 'followback',
            'followme', 'likeme', 'likeforlike', 'followforfollow'
        ]
        
        hashtag_lower = hashtag.lower().replace('#', '')
        
        return any(pattern in hashtag_lower for pattern in spam_patterns)
    
    def _validate_hashtag_count(self, hashtags: List[str], preset_type: str) -> List[str]:
        """
        Ensure hashtag count is within 8-12 range.
        
        Validates Requirement 10.1: Generate 8-12 hashtags
        """
        # Remove duplicates while preserving order
        seen = set()
        unique_hashtags = []
        for tag in hashtags:
            tag_lower = tag.lower()
            if tag_lower not in seen:
                seen.add(tag_lower)
                unique_hashtags.append(tag)
        
        # If too few, add fallback hashtags
        if len(unique_hashtags) < self.MIN_HASHTAGS:
            logger.warning(
                f"Only {len(unique_hashtags)} hashtags generated, adding fallbacks"
            )
            fallback = self._get_fallback_hashtags(preset_type)
            for tag in fallback:
                if tag.lower() not in seen and len(unique_hashtags) < self.MAX_HASHTAGS:
                    unique_hashtags.append(tag)
                    seen.add(tag.lower())
        
        # If too many, truncate to max
        if len(unique_hashtags) > self.MAX_HASHTAGS:
            logger.info(f"Truncating {len(unique_hashtags)} hashtags to {self.MAX_HASHTAGS}")
            unique_hashtags = unique_hashtags[:self.MAX_HASHTAGS]
        
        return unique_hashtags
    
    def _get_fallback_hashtags(self, preset_type: str) -> List[str]:
        """Get fallback hashtags for the given preset type."""
        fallback_sets = {
            "luxury": [
                "#luxury", "#luxurylifestyle", "#elegance", "#sophisticated",
                "#highend", "#premium", "#exclusive", "#lifestyle",
                "#fashion", "#style", "#instagood", "#photooftheday"
            ],
            "lifestyle": [
                "#lifestyle", "#lifestyleblogger", "#dailylife", "#authentic",
                "#reallife", "#moments", "#memories", "#adventure",
                "#explore", "#inspiration", "#instagood", "#photooftheday"
            ],
            "beauty": [
                "#beauty", "#beautyblogger", "#confidence", "#selfcare",
                "#naturalbeauty", "#style", "#fashion", "#glam",
                "#makeup", "#skincare", "#instagood", "#photooftheday"
            ]
        }
        
        return fallback_sets.get(
            preset_type.lower(),
            fallback_sets["lifestyle"]
        )[:self.MAX_HASHTAGS]
    
    async def close(self):
        """Close the OpenAI client."""
        await self.client.close()
