import pytest
from fastapi.testclient import TestClient
from app.main import app

# Create a single TestClient instance that all tests can use
@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)