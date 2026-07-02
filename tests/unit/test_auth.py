from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status

from app.api.schemas import UserCreate
from app.db.models import Role, User
from app.services.auth_service import AuthService


@pytest.fixture
def auth_service():
    mock_db = MagicMock()
    mock_user_repo = MagicMock()
    mock_role_repo = MagicMock()

    # We mock the security functions to avoid actual hashing overhead in basic unit tests
    return AuthService(db=mock_db, user_repo=mock_user_repo, role_repo=mock_role_repo)


def test_register_user_success(auth_service, mocker):
    # Arrange
    user_in = UserCreate(
        username="testuser",
        email="test@test.com",
        password="password123",
        repeat_password="password123",
    )

    auth_service.role_repo.get_role_by_name.return_value = Role(id=1, name="Participant")
    auth_service.user_repo.get_user_by_email.return_value = None

    mocker.patch("app.services.auth_service.get_password_hash", return_value="hashed_pw")

    # Act
    new_user = auth_service.register_user(user_in)

    # Assert
    assert new_user.username == "testuser"
    assert new_user.email == "test@test.com"
    assert new_user.hashed_password == "hashed_pw"
    auth_service.user_repo.add_user.assert_called_once_with(new_user)
    auth_service.db.commit.assert_called_once()
    auth_service.db.refresh.assert_called_once_with(new_user)


def test_register_user_missing_default_role(auth_service):
    # Arrange
    user_in = UserCreate(
        username="testuser",
        email="test@test.com",
        password="password123",
        repeat_password="password123",
    )
    auth_service.role_repo.get_role_by_name.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        auth_service.register_user(user_in)

    assert exc.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert "System configuration error" in exc.value.detail


def test_register_user_email_exists(auth_service):
    # Arrange
    user_in = UserCreate(
        username="testuser",
        email="test@test.com",
        password="password123",
        repeat_password="password123",
    )
    auth_service.role_repo.get_role_by_name.return_value = Role(id=1, name="Participant")
    auth_service.user_repo.get_user_by_email.return_value = User(id=1)  # Simulating existing user

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        auth_service.register_user(user_in)

    assert exc.value.status_code == status.HTTP_400_BAD_REQUEST
    assert exc.value.detail == "Email already registered"


def test_authenticate_user_success(auth_service, mocker):
    # Arrange
    mock_user = User(id=1, username="testuser", hashed_password="hashed_pw")
    auth_service.user_repo.get_user_by_username.return_value = mock_user

    mocker.patch("app.services.auth_service.verify_password", return_value=True)
    mocker.patch("app.services.auth_service.create_access_token", return_value="mock_jwt_token")

    # Act
    response = auth_service.authenticate_user("testuser", "password123")

    # Assert
    assert response["access_token"] == "mock_jwt_token"
    assert response["token_type"] == "bearer"


def test_authenticate_user_invalid_credentials(auth_service, mocker):
    # Arrange
    auth_service.user_repo.get_user_by_username.return_value = None

    # Act & Assert
    with pytest.raises(HTTPException) as exc:
        auth_service.authenticate_user("wronguser", "wrongpass")

    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED
    assert exc.value.detail == "Incorrect username or password"
