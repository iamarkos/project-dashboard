from app.api.schemas import ProjectInvite, ProjectInviteResponse, ProjectUpdate  # Added import
from app.core.enums import ProjectRole
from app.db.models import Project, ProjectParticipant, User
from app.repositories.participant_repository import ParticipantRepository
from app.repositories.project_repository import ProjectRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository


class ProjectService:
    def __init__(
        self,
        project_repo: ProjectRepository,
        participant_repo: ParticipantRepository,
        user_repo: UserRepository,
        role_repo: RoleRepository,
    ):
        self.project_repo = project_repo
        self.participant_repo = participant_repo
        self.user_repo = user_repo
        self.role_repo = role_repo

    def create_project(
        self,
        owner: User,
        title: str,
        description: str,
    ) -> Project:
        # Get the owner role
        owner_role = self.role_repo.get_role_by_name(ProjectRole.OWNER.value)
        if not owner_role:
            raise RuntimeError("System configurayion error: Owner role not found.")

        # Create the model
        project = Project(title=title, description=description, created_by=owner.id)
        
        # Create the participant link
        participant = ProjectParticipant(
            project=project,
            user=owner,
            role=owner_role,
        )

        return self.project_repo.add_project(project, participant)

    def get_projects(
        self,
        current_user: User,
    ) -> list[Project]:
        return self.project_repo.list_for_user(current_user.id)

    def update_project(
        self, project_id: int, current_user: User, project_in: ProjectUpdate
    ) -> Project | None:
        user_id = current_user.id
        if not self.participant_repo.has_access(project_id, user_id):
            raise PermissionError(
                "Project not found or you have no access."
            )

        project = self.project_repo.get_by_id(project_id)
        if not project:
            raise ValueError(
                "Project not found."
            )

        # Apply updates
        update_data = project_in.model_dump(exclude_unset=True)
        updated_project = self.project_repo.update(project, update_data)

        return self.project_repo.update(project, update_data)

    def delete_project(self, project_id: int, current_user: User) -> None:
        user_id = current_user.id
        if not self.participant_repo.is_owner(project_id, user_id):
            raise PermissionError(
                "Only the project owner can delete this project."
            )

        project = self.project_repo.get_by_id(project_id)
        if project:
            self.project_repo.delete_project(project)

    def invite_user(
        self,
        project_id: int,
        current_user: User,
        invite_in: ProjectInvite,
    ) -> ProjectInviteResponse:
        user_id = current_user.id

        if not self.participant_repo.is_owner(project_id, user_id):
            raise PermissionError(
                "Only the project owner can invite users."
            )

        user_to_invite = self.user_repo.get_user_by_id(invite_in.user_id)
        if not user_to_invite:
            raise ValueError(
                "User to invite not found."
            )

        role = self.role_repo.get_role_by_id(invite_in.role_id)
        if not role:
            raise ValueError("Role not found.")

        if self.participant_repo.has_access(project_id, invite_in.user_id):
            raise ValueError(
                "User is already a participant in this project."
            )

        new_participant = ProjectParticipant(
            project_id=project_id, user_id=invite_in.user_id, role_id=invite_in.role_id
        )

        self.project_repo.add_participant(new_participant)

        return ProjectInviteResponse(
            project_id=project_id,
            user_id=invite_in.user_id,
            role_name=role.name,
        )
