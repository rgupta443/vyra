"""
Test configuration and fixtures.
"""
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Set test environment variables before importing the app
os.environ.update({
    "SECRET_KEY": "test-secret-key-for-testing-only",
    "POSTGRES_SERVER": "localhost",
    "POSTGRES_USER": "postgres",
    "POSTGRES_PASSWORD": "postgres",
    "POSTGRES_DB": "instagram_automation",
    "OPENAI_API_KEY": "test-openai-key",
    "NANO_BANANA_API_KEY": "test-nano-banana-key",
    "STRIPE_SECRET_KEY": "sk_test_test_key",
    "STRIPE_PUBLISHABLE_KEY": "pk_test_test_key",
    "STRIPE_WEBHOOK_SECRET": "whsec_test_secret",
    "ENVIRONMENT": "testing"
})

from app.main import app
from app.core.database import Base, get_db


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)


@pytest.fixture
def db():
    """Create a test database session."""
    from app.core.database import SessionLocal
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()