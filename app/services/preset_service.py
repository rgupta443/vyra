"""
Preset configuration service for managing generation templates.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from uuid import UUID

from app.models.preset import PresetConfig
from app.models.generation import PresetType
from app.schemas.preset import (
    PresetConfigCreate,
    PresetConfigUpdate,
    PresetValidationResult,
    BrandSafetyRules
)


class PresetService:
    """Service for managing preset configurations."""
    
    # Default brand safety rules applied to all presets
    DEFAULT_BRAND_SAFETY_RULES = {
        "forbidden_terms": [
            "sexy", "seductive", "provocative", "sultry", "sensual",
            "revealing", "exposed", "nude", "naked", "explicit"
        ],
        "forbidden_poses": [
            "lying down suggestively", "bedroom poses", "intimate poses",
            "provocative angles", "suggestive positioning"
        ],
        "forbidden_expressions": [
            "overly dramatic", "extreme emotions", "exaggerated reactions",
            "unnatural expressions", "forced smiles"
        ],
        "forbidden_aesthetics": [
            "cheap filters", "low quality effects", "oversaturated colors",
            "heavy vignetting", "excessive blur", "amateur lighting"
        ],
        "quality_standards": [
            "professional lighting",
            "natural expressions",
            "high resolution output",
            "photorealistic rendering",
            "brand-appropriate composition"
        ]
    }
    
    # Preset templates with brand-safe configurations
    PRESET_TEMPLATES = {
        PresetType.LUXURY: {
            "name": "luxury",
            "prompt_template": "Professional portrait in luxury setting, elegant and sophisticated, high-end fashion photography style, natural lighting, photorealistic, 4K quality",
            "style_parameters": {
                "identity_strength": 0.95,
                "collage": False,
                "sprite_mode": False,
                "quality": "high",
                "aesthetic": "luxury",
                "lighting": "professional",
                "composition": "elegant"
            },
            "brand_safety_rules": DEFAULT_BRAND_SAFETY_RULES
        },
        PresetType.LIFESTYLE: {
            "name": "lifestyle",
            "prompt_template": "Lifestyle portrait in natural setting, casual and authentic, editorial photography style, natural daylight, photorealistic, 4K quality",
            "style_parameters": {
                "identity_strength": 0.95,
                "collage": False,
                "sprite_mode": False,
                "quality": "high",
                "aesthetic": "lifestyle",
                "lighting": "natural",
                "composition": "casual"
            },
            "brand_safety_rules": DEFAULT_BRAND_SAFETY_RULES
        },
        PresetType.BEAUTY: {
            "name": "beauty",
            "prompt_template": "Beauty portrait with clean background, professional makeup and styling, beauty photography style, soft studio lighting, photorealistic, 4K quality",
            "style_parameters": {
                "identity_strength": 0.95,
                "collage": False,
                "sprite_mode": False,
                "quality": "high",
                "aesthetic": "beauty",
                "lighting": "studio",
                "composition": "clean"
            },
            "brand_safety_rules": DEFAULT_BRAND_SAFETY_RULES
        }
    }
    
    @staticmethod
    def validate_preset_parameters(style_parameters: Dict[str, Any]) -> PresetValidationResult:
        """
        Validate preset parameters for brand safety and technical requirements.
        
        Args:
            style_parameters: Dictionary of style parameters to validate
            
        Returns:
            PresetValidationResult with validation status and any errors/warnings
        """
        errors = []
        warnings = []
        
        # Validate identity strength
        identity_strength = style_parameters.get('identity_strength', 0.95)
        if identity_strength < 0.95:
            errors.append(f"Identity strength {identity_strength} is below minimum 0.95")
        elif identity_strength < 0.97:
            warnings.append(f"Identity strength {identity_strength} is below recommended 0.97")
        
        # Validate anti-collage enforcement
        if style_parameters.get('collage', False) is not False:
            errors.append("Collage mode must be disabled (set to false)")
        
        if style_parameters.get('sprite_mode', False) is not False:
            errors.append("Sprite mode must be disabled (set to false)")
        
        # Validate quality setting
        quality = style_parameters.get('quality', 'high')
        if quality not in ['high', 'ultra', 'maximum']:
            warnings.append(f"Quality setting '{quality}' may not meet brand standards")
        
        return PresetValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def validate_brand_safety_rules(brand_safety_rules: Dict[str, Any]) -> PresetValidationResult:
        """
        Validate brand safety rules are properly configured.
        
        Args:
            brand_safety_rules: Dictionary of brand safety rules
            
        Returns:
            PresetValidationResult with validation status
        """
        errors = []
        warnings = []
        
        required_keys = ['forbidden_terms', 'forbidden_poses', 'forbidden_expressions', 
                        'forbidden_aesthetics', 'quality_standards']
        
        for key in required_keys:
            if key not in brand_safety_rules:
                warnings.append(f"Missing brand safety rule category: {key}")
        
        # Ensure forbidden lists are not empty
        if not brand_safety_rules.get('forbidden_terms'):
            warnings.append("No forbidden terms defined - consider adding brand safety terms")
        
        if not brand_safety_rules.get('quality_standards'):
            warnings.append("No quality standards defined - consider adding quality requirements")
        
        return PresetValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    @staticmethod
    def enforce_brand_safety(prompt: str, brand_safety_rules: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Check if a prompt violates brand safety rules.
        
        Args:
            prompt: The generation prompt to check
            brand_safety_rules: Dictionary of brand safety rules
            
        Returns:
            Tuple of (is_safe, violation_reason)
        """
        prompt_lower = prompt.lower()
        
        # Check forbidden terms
        forbidden_terms = brand_safety_rules.get('forbidden_terms', [])
        for term in forbidden_terms:
            if term.lower() in prompt_lower:
                return False, f"Prompt contains forbidden term: {term}"
        
        # Check forbidden poses
        forbidden_poses = brand_safety_rules.get('forbidden_poses', [])
        for pose in forbidden_poses:
            if pose.lower() in prompt_lower:
                return False, f"Prompt contains forbidden pose: {pose}"
        
        # Check forbidden expressions
        forbidden_expressions = brand_safety_rules.get('forbidden_expressions', [])
        for expression in forbidden_expressions:
            if expression.lower() in prompt_lower:
                return False, f"Prompt contains forbidden expression: {expression}"
        
        # Check forbidden aesthetics
        forbidden_aesthetics = brand_safety_rules.get('forbidden_aesthetics', [])
        for aesthetic in forbidden_aesthetics:
            if aesthetic.lower() in prompt_lower:
                return False, f"Prompt contains forbidden aesthetic: {aesthetic}"
        
        return True, None
    
    @staticmethod
    def get_preset_by_type(db: Session, preset_type: PresetType) -> Optional[PresetConfig]:
        """
        Get preset configuration by type.
        
        Args:
            db: Database session
            preset_type: Type of preset to retrieve
            
        Returns:
            PresetConfig if found, None otherwise
        """
        return db.query(PresetConfig).filter(
            PresetConfig.name == preset_type.value,
            PresetConfig.is_active == True
        ).first()
    
    @staticmethod
    def get_all_active_presets(db: Session) -> List[PresetConfig]:
        """
        Get all active preset configurations.
        
        Args:
            db: Database session
            
        Returns:
            List of active PresetConfig objects
        """
        return db.query(PresetConfig).filter(
            PresetConfig.is_active == True
        ).all()
    
    @staticmethod
    def create_preset(db: Session, preset_data: PresetConfigCreate) -> tuple[Optional[PresetConfig], Optional[str]]:
        """
        Create a new preset configuration.
        
        Args:
            db: Database session
            preset_data: Preset configuration data
            
        Returns:
            Tuple of (PresetConfig, error_message)
        """
        # Validate parameters
        param_validation = PresetService.validate_preset_parameters(preset_data.style_parameters)
        if not param_validation.is_valid:
            return None, f"Invalid parameters: {', '.join(param_validation.errors)}"
        
        # Validate brand safety rules
        safety_validation = PresetService.validate_brand_safety_rules(preset_data.brand_safety_rules)
        if not safety_validation.is_valid:
            return None, f"Invalid brand safety rules: {', '.join(safety_validation.errors)}"
        
        # Check if preset with same name exists
        existing = db.query(PresetConfig).filter(
            PresetConfig.name == preset_data.name
        ).first()
        
        if existing:
            return None, f"Preset with name '{preset_data.name}' already exists"
        
        # Create preset
        preset = PresetConfig(
            name=preset_data.name,
            prompt_template=preset_data.prompt_template,
            style_parameters=preset_data.style_parameters,
            brand_safety_rules=preset_data.brand_safety_rules,
            is_active=preset_data.is_active
        )
        
        db.add(preset)
        db.commit()
        db.refresh(preset)
        
        return preset, None
    
    @staticmethod
    def update_preset(
        db: Session,
        preset_id: UUID,
        preset_data: PresetConfigUpdate
    ) -> tuple[Optional[PresetConfig], Optional[str]]:
        """
        Update an existing preset configuration.
        
        Args:
            db: Database session
            preset_id: ID of preset to update
            preset_data: Updated preset data
            
        Returns:
            Tuple of (PresetConfig, error_message)
        """
        preset = db.query(PresetConfig).filter(PresetConfig.id == preset_id).first()
        if not preset:
            return None, "Preset not found"
        
        # Validate parameters if provided
        if preset_data.style_parameters:
            param_validation = PresetService.validate_preset_parameters(preset_data.style_parameters)
            if not param_validation.is_valid:
                return None, f"Invalid parameters: {', '.join(param_validation.errors)}"
            preset.style_parameters = preset_data.style_parameters
        
        # Validate brand safety rules if provided
        if preset_data.brand_safety_rules:
            safety_validation = PresetService.validate_brand_safety_rules(preset_data.brand_safety_rules)
            if not safety_validation.is_valid:
                return None, f"Invalid brand safety rules: {', '.join(safety_validation.errors)}"
            preset.brand_safety_rules = preset_data.brand_safety_rules
        
        # Update other fields
        if preset_data.prompt_template is not None:
            preset.prompt_template = preset_data.prompt_template
        
        if preset_data.is_active is not None:
            preset.is_active = preset_data.is_active
        
        db.commit()
        db.refresh(preset)
        
        return preset, None
    
    @staticmethod
    def initialize_default_presets(db: Session) -> List[PresetConfig]:
        """
        Initialize default preset configurations if they don't exist.
        
        Args:
            db: Database session
            
        Returns:
            List of created/existing PresetConfig objects
        """
        presets = []
        
        for preset_type, template in PresetService.PRESET_TEMPLATES.items():
            # Check if preset already exists
            existing = db.query(PresetConfig).filter(
                PresetConfig.name == template['name']
            ).first()
            
            if existing:
                presets.append(existing)
                continue
            
            # Create new preset
            preset = PresetConfig(
                name=template['name'],
                prompt_template=template['prompt_template'],
                style_parameters=template['style_parameters'],
                brand_safety_rules=template['brand_safety_rules'],
                is_active=True
            )
            
            db.add(preset)
            presets.append(preset)
        
        db.commit()
        
        return presets
