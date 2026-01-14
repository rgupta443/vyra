#!/usr/bin/env python3
"""
Script to initialize default preset configurations in the database.
"""
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.database import SessionLocal
from app.services.preset_service import PresetService
from app.models.generation import PresetType


def init_presets():
    """Initialize default preset configurations."""
    print("Initializing default preset configurations...")
    
    db = SessionLocal()
    try:
        presets = PresetService.initialize_default_presets(db)
        
        print(f"\n✓ Successfully initialized {len(presets)} presets:")
        for preset in presets:
            print(f"  - {preset.name.upper()}: {preset.prompt_template[:60]}...")
            print(f"    Identity Strength: {preset.style_parameters.get('identity_strength')}")
            print(f"    Collage: {preset.style_parameters.get('collage')}")
            print(f"    Sprite Mode: {preset.style_parameters.get('sprite_mode')}")
            print(f"    Active: {preset.is_active}")
            print()
        
        print("✓ Preset initialization complete!")
        
    except Exception as e:
        print(f"✗ Error initializing presets: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    init_presets()
