from typing import Any

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.api.schemas import UserCreate, UserResponse
from app.core.security import create_access_token, verify_password
from app.db.models import Role, User

router = APIRouter(tags=["Authentication"])


@router.post("/auth", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)) -> Any:

    # 1. Prevent Foreign Key Crash: Ensure a default role exists
    default_role = db.query(Role).filter(Role.name == "Participant").first()
    if not default_role:
        raise HTTPException(
            status_code=500, detail="System configuration error: Role 'Participant' not found."
        )
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


@router.post("/login")
def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)
) -> dict[str, str]:
    # 1. Find user by username
    user = db.query(User).filter(User.username == form_data.username).first()

    # 2. Verify user exists and password matches
    if not user or not verify_password(form_data.password, str(user.hashed_password)):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 3. Generate JWT
    access_token = create_access_token(data={"sub": str(user.id)})

    # 4. Return standard OAuth2 response
    return {"access_token": access_token, "token_type": "bearer"}
