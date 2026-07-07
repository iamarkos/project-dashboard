from fastapi import Depends
from sqlalchemy.orm import Session, selectinload

from app.db.database import get_db
from app.db.models import Project, ProjectParticipant


class ProjectRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def add_project(self, project: Project, participant: ProjectParticipant) -> Project:

        # Add both to the session
        self.db.add(project)
        self.db.add(participant)

        # Commit the transaction once
        self.db.commit()
        self.db.refresh(project)

        return project

    def add_participant(self, participant: ProjectParticipant) -> None:
        self.db.add(participant)
        self.db.commit()

    def get_by_id(
        self,
        project_id: int,
    ) -> Project | None:
        return self.db.query(Project).options(selectinload(Project.documents)).filter(Project.id == project_id).first()

    def list_for_user(
        self,
        user_id: int,
    ) -> list[Project]:
        return (
            self.db.query(Project)
            .join(ProjectParticipant)
            .options(selectinload(Project.documents))
            .filter(ProjectParticipant.user_id == user_id)
            .all()
        )

    def update(self, project: Project, update_data: dict[str, str]) -> Project:
        for key, value in update_data.items():
            setattr(project, key, value)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete_project(self, project: Project) -> None:
        self.db.delete(project)
        self.db.commit()
