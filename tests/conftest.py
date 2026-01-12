"""
Test configuration and fixtures.
"""
import os
import pytest
from fastapi.testclient import TestClient

# Set test environment variables before importing the app
os.environ.update({
    "SECRET_KEY": "test-secret-key-for-testing-only",
    "POSTGRES_SERVER": "localhost",
    "POSTGRES_USER": "test_user",
    "POSTGRES_PASSWORD": "test_password",
    "POSTGRES_DB": "test_db",
    "OPENAI_API_KEY": "test-openai-key",
    "NANO_BANANA_API_KEY": "test-nano-banana-key",
    "STRIPE_SECRET_KEY": "sk_test_test_key",
    "STRIPE_PUBLISHABLE_KEY": "pk_test_test_key",
    "STRIPE_WEBHOOK_SECRET": "whsec_test_secret",
    "ENVIRONMENT": "testing"
})

from app.main import app


@pytest.fixture
def client():
    """Create a test client."""
    return TestClient(app)