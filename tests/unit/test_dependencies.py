from unittest.mock import MagicMock

import pytest
from fastapi import HTTPException, status
from jwt.exceptions import InvalidTokenError

from app.api.dependencies import get_current_user, require_owner, require_project_access
from app.db.models import Project, User


def test_get_current_user_success(mocker):
    mock_repo = MagicMock()
    mock_user = User(id=1, username="testuser")
    mock_repo.get_user_by_id.return_value = mock_user

    mocker.patch("app.api.dependencies.decode_access_token", return_value={"sub": "1"})

    user = get_current_user(token="valid_token", user_repo=mock_repo)
    assert user.id == 1


def test_get_current_user_invalid_token(mocker):
    mock_repo = MagicMock()
    mocker.patch("app.api.dependencies.decode_access_token", side_effect=InvalidTokenError)

    with pytest.raises(HTTPException) as exc:
        get_current_user(token="invalid_token", user_repo=mock_repo)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_missing_sub(mocker):
    mock_repo = MagicMock()
    mocker.patch("app.api.dependencies.decode_access_token", return_value={})  # No 'sub'

    with pytest.raises(HTTPException) as exc:
        get_current_user(token="token", user_repo=mock_repo)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_get_current_user_not_found(mocker):
    mock_repo = MagicMock()
    mock_repo.get_user_by_id.return_value = None
    mocker.patch("app.api.dependencies.decode_access_token", return_value={"sub": "99"})

    with pytest.raises(HTTPException) as exc:
        get_current_user(token="token", user_repo=mock_repo)
    assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


def test_require_project_access_success():
    mock_project_repo = MagicMock()
    mock_participant_repo = MagicMock()
    mock_user = User(id=1)
    mock_project = Project(id=10)

    mock_project_repo.get_by_id.return_value = mock_project
    mock_participant_repo.has_access.return_value = True

    project = require_project_access(10, mock_user, mock_project_repo, mock_participant_repo)
    assert project.id == 10


def test_require_project_access_not_found():
    mock_project_repo = MagicMock()
    mock_participant_repo = MagicMock()
    mock_user = User(id=1)

    mock_project_repo.get_by_id.return_value = None

    with pytest.raises(HTTPException) as exc:
        require_project_access(99, mock_user, mock_project_repo, mock_participant_repo)
    assert exc.value.status_code == 404


def test_require_project_access_forbidden():
    mock_project_repo = MagicMock()
    mock_participant_repo = MagicMock()
    mock_user = User(id=1)

    mock_project_repo.get_by_id.return_value = Project(id=10)
    mock_participant_repo.has_access.return_value = False

    with pytest.raises(HTTPException) as exc:
        require_project_access(10, mock_user, mock_project_repo, mock_participant_repo)
    assert exc.value.status_code == 403


def test_require_owner_success():
    mock_project_repo = MagicMock()
    mock_participant_repo = MagicMock()
    mock_user = User(id=1)
    mock_project = Project(id=10)

    mock_project_repo.get_by_id.return_value = mock_project
    mock_participant_repo.is_owner.return_value = True

    project = require_owner(10, mock_user, mock_project_repo, mock_participant_repo)
    assert project.id == 10


def test_require_owner_forbidden():
    mock_project_repo = MagicMock()
    mock_participant_repo = MagicMock()
    mock_user = User(id=1)

    mock_project_repo.get_by_id.return_value = Project(id=10)
    mock_participant_repo.is_owner.return_value = False

    with pytest.raises(HTTPException) as exc:
        require_owner(10, mock_user, mock_project_repo, mock_participant_repo)
    assert exc.value.status_code == 403
