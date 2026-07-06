from unittest.mock import MagicMock

import pytest

from app.api.schemas import ProjectInvite, ProjectUpdate
from app.core.enums import ProjectRole
from app.db.models import Project, Role, User
from app.services.project_service import ProjectService


@pytest.fixture
def project_service():
    return ProjectService(
        project_repo=MagicMock(),
        participant_repo=MagicMock(),
        user_repo=MagicMock(),
        role_repo=MagicMock(),
    )


def test_create_project_success(project_service):
    owner = User(id=1, username="owner")
    mock_role = Role(id=1, name=ProjectRole.OWNER.value)
    project_service.role_repo.get_role_by_name.return_value = mock_role

    project_service.project_repo.add_project.side_effect = lambda p, part: p

    project = project_service.create_project(owner=owner, title="New Project", description="Desc")

    assert project.title == "New Project"
    assert project.created_by == 1
    project_service.project_repo.add_project.assert_called_once()


def test_update_project_no_access(project_service):
    user = User(id=1)
    update_data = ProjectUpdate(title="Updated Title")

    project_service.participant_repo.has_access.return_value = False

    with pytest.raises(PermissionError) as exc:
        project_service.update_project(project_id=10, current_user=user, project_in=update_data)

    assert "no access" in str(exc.value)


def test_delete_project_not_owner(project_service):
    user = User(id=2)
    project_service.participant_repo.is_owner.return_value = False

    with pytest.raises(PermissionError) as exc:
        project_service.delete_project(project_id=1, current_user=user)

    assert "Only the project owner" in str(exc.value)


def test_invite_user_success(project_service):
    owner = User(id=1)
    invite_in = ProjectInvite(user_id=2, role_id=2)

    project_service.participant_repo.is_owner.return_value = True
    project_service.user_repo.get_user_by_id.return_value = User(id=2)
    project_service.role_repo.get_role_by_id.return_value = Role(id=2, name="Viewer")
    project_service.participant_repo.has_access.return_value = False  # Not already in project

    response = project_service.invite_user(project_id=10, current_user=owner, invite_in=invite_in)

    assert response.project_id == 10
    assert response.user_id == 2
    assert response.role_name == "Viewer"
    project_service.project_repo.add_participant.assert_called_once()


def test_invite_user_already_participant(project_service):
    owner = User(id=1)
    invite_in = ProjectInvite(user_id=2, role_id=2)

    project_service.participant_repo.is_owner.return_value = True
    project_service.user_repo.get_user_by_id.return_value = User(id=2)
    project_service.role_repo.get_role_by_id.return_value = Role(id=2, name="Viewer")
    project_service.participant_repo.has_access.return_value = True  # Already in project!

    with pytest.raises(ValueError) as exc:
        project_service.invite_user(project_id=10, current_user=owner, invite_in=invite_in)

    assert "already a participant" in str(exc.value)


def test_create_project_missing_role(project_service):
    owner = User(id=1)
    project_service.role_repo.get_role_by_name.return_value = None

    with pytest.raises(RuntimeError) as exc:
        project_service.create_project(owner=owner, title="Title", description="Desc")
    assert "role not found" in str(exc.value)


def test_get_projects_success(project_service):
    user = User(id=1)
    mock_projects = [Project(id=1, title="A"), Project(id=2, title="B")]
    project_service.project_repo.list_for_user.return_value = mock_projects

    projects = project_service.get_projects(current_user=user)
    assert len(projects) == 2


def test_update_project_success(project_service):
    user = User(id=1)
    project = Project(id=10, title="Old")
    update_data = ProjectUpdate(title="New Title")

    project_service.participant_repo.has_access.return_value = True
    project_service.project_repo.get_by_id.return_value = project
    project_service.project_repo.update.return_value = Project(id=10, title="New Title")

    updated = project_service.update_project(
        project_id=10, current_user=user, project_in=update_data
    )
    assert updated.title == "New Title"


def test_update_project_not_found(project_service):
    user = User(id=1)
    update_data = ProjectUpdate(title="New Title")

    project_service.participant_repo.has_access.return_value = True
    project_service.project_repo.get_by_id.return_value = None  # Not found

    with pytest.raises(ValueError) as exc:
        project_service.update_project(project_id=99, current_user=user, project_in=update_data)
    assert "Project not found" in str(exc.value)


def test_delete_project_success(project_service):
    user = User(id=1)
    project = Project(id=10)

    project_service.participant_repo.is_owner.return_value = True
    project_service.project_repo.get_by_id.return_value = project

    project_service.delete_project(project_id=10, current_user=user)

    project_service.project_repo.delete_project.assert_called_once_with(project)


def test_invite_user_target_not_found(project_service):
    owner = User(id=1)
    invite_in = ProjectInvite(user_id=99, role_id=2)

    project_service.participant_repo.is_owner.return_value = True
    project_service.user_repo.get_user_by_id.return_value = None  # User doesn't exist

    with pytest.raises(ValueError) as exc:
        project_service.invite_user(project_id=10, current_user=owner, invite_in=invite_in)
    assert "User to invite not found" in str(exc.value)


def test_invite_user_role_not_found(project_service):
    owner = User(id=1)
    invite_in = ProjectInvite(user_id=2, role_id=99)

    project_service.participant_repo.is_owner.return_value = True
    project_service.user_repo.get_user_by_id.return_value = User(id=2)
    project_service.role_repo.get_role_by_id.return_value = None  # Role doesn't exist

    with pytest.raises(ValueError) as exc:
        project_service.invite_user(project_id=10, current_user=owner, invite_in=invite_in)
    assert "Role not found" in str(exc.value)
