#!/usr/bin/env python3
"""
Setup verification script for Instagram Content Automation.
"""
import sys
import importlib.util

def check_imports():
    """Check that all required modules can be imported."""
    required_modules = [
        'fastapi',
        'uvicorn',
        'sqlalchemy',
        'alembic',
        'redis',
        'rq',
        'pydantic',
        'pydantic_settings',
        'jose',
        'passlib',
        'httpx',
        'pytest',
        'hypothesis'
    ]
    
    print("Checking required modules...")
    failed_imports = []
    
    for module in required_modules:
        try:
            importlib.import_module(module)
            print(f"✓ {module}")
        except ImportError as e:
            print(f"✗ {module}: {e}")
            failed_imports.append(module)
    
    if failed_imports:
        print(f"\nFailed to import: {', '.join(failed_imports)}")
        return False
    
    print("\nAll required modules imported successfully!")
    return True


def check_app_structure():
    """Check that the app can be imported and basic structure exists."""
    print("\nChecking application structure...")
    
    try:
        from app.main import app
        print("✓ FastAPI app imported successfully")
        
        from app.core.config import settings
        print("✓ Settings configuration loaded")
        
        from app.core.database import Base, get_db
        print("✓ Database configuration loaded")
        
        from app.core.redis import get_redis
        print("✓ Redis configuration loaded")
        
        from app.models.user import User
        from app.models.face import Face
        from app.models.generation import Generation
        from app.models.preset import PresetConfig
        print("✓ Database models imported")
        
        from app.worker.tasks import generate_image_task
        print("✓ Worker tasks imported")
        
        print("\nApplication structure verified!")
        return True
        
    except Exception as e:
        print(f"✗ Application structure check failed: {e}")
        return False


def main():
    """Run all setup checks."""
    print("Instagram Content Automation - Setup Verification")
    print("=" * 50)
    
    checks_passed = 0
    total_checks = 2
    
    if check_imports():
        checks_passed += 1
    
    if check_app_structure():
        checks_passed += 1
    
    print("\n" + "=" * 50)
    print(f"Setup verification complete: {checks_passed}/{total_checks} checks passed")
    
    if checks_passed == total_checks:
        print("✓ Setup is ready for development!")
        return 0
    else:
        print("✗ Setup has issues that need to be resolved.")
        return 1


if __name__ == "__main__":
    sys.exit(main())