from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.enums import ProjectRole
from app.db.database import get_db
from app.db.models import ProjectParticipant, Role


class ParticipantRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_participation(
        self,
        project_id: int,
        user_id: int,
    ) -> ProjectParticipant | None:

        return (
            self.db.query(ProjectParticipant)
            .filter(
                ProjectParticipant.project_id == project_id,
                ProjectParticipant.user_id == user_id,
            )
            .first()
        )

    def is_owner(
        self,
        project_id: int,
        user_id: int,
    ) -> bool:
        participant = (
            self.db.query(ProjectParticipant)
            .join(Role)
            .filter(
                ProjectParticipant.project_id == project_id,
                ProjectParticipant.user_id == user_id,
                Role.name == ProjectRole.OWNER.value,
            )
            .first()
        )

        return participant is not None

    def has_access(
        self,
        project_id: int,
        user_id: int,
    ) -> bool:
        return (
            self.get_participation(
                project_id,
                user_id,
            )
            is not None
        )
