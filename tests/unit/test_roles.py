from unittest.mock import MagicMock

import pytest

from app.core.enums import ProjectRole
from app.db.models import Role
from app.services.role_service import RoleService


def test_get_owner_role_success():
    mock_db = MagicMock()
    mock_role = Role(id=1, name=ProjectRole.OWNER.value)

    # Mocking the SQLAlchemy query chain: db.query().filter().first()
    mock_db.query.return_value.filter.return_value.first.return_value = mock_role

    service = RoleService(db=mock_db)
    role = service.get_owner_role()

    assert role.name == ProjectRole.OWNER.value


def test_get_owner_role_missing():
    mock_db = MagicMock()
    mock_db.query.return_value.filter.return_value.first.return_value = None

    service = RoleService(db=mock_db)

    with pytest.raises(RuntimeError) as exc:
        service.get_owner_role()
    assert "Owner role is missing" in str(exc.value)
