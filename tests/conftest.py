import uuid

import pytest
from fastapi.testclient import TestClient
from moto import mock_aws
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.dependencies import get_db
from app.db import database
from app.main import app

# Use the secure URL from your environment variables
engine = create_engine(database.SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db_session):
    # Override the get_db dependency to use our testing session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    # Clear overrides after the test
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(client: TestClient) -> dict:
    """Creates a unique user and returns the Authorization header."""
    unique_id = uuid.uuid4()
    username = f"proj_user_{unique_id.hex[:8]}"
    password = "testpassword123"

    # 1. Register
    client.post(
        "/auth",
        json={"username": username, "email": f"{username}@example.com", "password": password},
    )
    # 2. Login
    login_response = client.post("/login", data={"username": username, "password": password})
    token = login_response.json()["access_token"]

    # 3. Return header
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def alt_auth_headers(client: TestClient) -> dict:
    """Creates a second, entirely separate user for testing access controls."""
    unique_id = uuid.uuid4()
    username = f"alt_user_{unique_id.hex[:8]}"
    password = "testpassword123"

    # Register and Login User B
    client.post(
        "/auth",
        json={"username": username, "email": f"{username}@example.com", "password": password},
    )
    login_response = client.post("/login", data={"username": username, "password": password})
    return {"Authorization": f"Bearer {login_response.json()['access_token']}"}


@pytest.fixture
def test_project(client: TestClient, auth_headers: dict) -> dict:
    """Creates a project and returns its data so other tests can use it."""
    payload = {"title": "Base Fixture Project", "description": "Used for testing"}
    response = client.post("/projects", json=payload, headers=auth_headers)
    return response.json()


@pytest.fixture(autouse=True)
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    import os

    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"


@pytest.fixture(autouse=True)
def mock_s3():
    with mock_aws():  # redirects all boto3 calls to a virtual bucket
        yield
