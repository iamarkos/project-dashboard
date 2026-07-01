from sqlalchemy.orm import Session

from app.core.enums import ProjectRole
from app.db.models import Role


class RoleService:
    def __init__(self, db: Session):
        self.db = db

    def get_owner_role(self) -> Role:
        role = self.db.query(Role).filter(Role.name == ProjectRole.OWNER.value).first()

        if role is None:
            raise RuntimeError("Owner role is missing.")

        return role
