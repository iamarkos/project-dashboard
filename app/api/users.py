from typing import Any, Generator

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas import UserCreate, UserResponse
from app.db.database import SessionLocal
from app.db.models import Role, User

# mini-FastAPI app just for user-related routes
router = APIRouter(prefix="/users", tags=["Users"])


# temporary database session
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> Any:

    # 1. Prevent Foreign Key Crash: Ensure a default role exists
    default_role = db.query(Role).filter(Role.name == "Participant").first()
    if not default_role:
        default_role = Role(name="Participant")
        db.add(default_role)
        db.commit()
        db.refresh(default_role)

    # 2. Check if the email exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    # 3. Hash the password
    hashed_pw = bcrypt.hashpw(user.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    # 4. Create the SQLAlchemy Object and save it
    new_user = User(
        username=user.username, email=user.email, hashed_password=hashed_pw, role_id=default_role.id
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
