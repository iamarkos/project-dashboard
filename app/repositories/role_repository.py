from fastapi import Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.db.models import Role


class RoleRepository:
    def __init__(self, db: Session = Depends(get_db)):
        self.db = db

    def get_role_by_name(self, name: str) -> Role | None:
        return self.db.query(Role).filter(Role.name == name).first()

    def get_role_by_id(self, role_id: int) -> Role | None:
        return self.db.query(Role).filter(Role.id == role_id).first()
