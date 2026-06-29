from typing import Generator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_password
from app.db.database import SessionLocal
from app.db.models import User

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


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
