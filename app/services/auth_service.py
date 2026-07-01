from fastapi import Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.schemas import UserCreate
from app.core.security import create_access_token, get_password_hash, verify_password
from app.db.database import get_db
from app.db.models import User
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository


class AuthService:
    def __init__(
        self,
        db: Session = Depends(get_db),
        user_repo: UserRepository = Depends(),
        role_repo: RoleRepository = Depends(),
    ):
        self.db = db
        self.user_repo = user_repo
        self.role_repo = role_repo

    def register_user(self, user_in: UserCreate) -> User:
        # Ensure a default role exists
        default_role = self.role_repo.get_role_by_name("Participant")
        if not default_role:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="System configuration error: Role 'Participant' not found.",
            )

        # Check if the email exists
        existing_user = self.user_repo.get_user_by_email(user_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
            )

        # Hash the password
        hashed_pw = get_password_hash(user_in.password)

        new_user = User(username=user_in.username, email=user_in.email, hashed_password=hashed_pw)

        self.user_repo.add_user(new_user)
        self.db.commit()
        self.db.refresh(new_user)

        return new_user

    def authenticate_user(self, username: str, password: str) -> dict[str, str]:
        # Find user by username
        user = self.user_repo.get_user_by_username(username)

        # Verify user exists and password matches
        if not user or not verify_password(password, str(user.hashed_password)):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Generate JWT
        access_token = create_access_token(data={"sub": str(user.id)})

        # Return standard OAuth2 response
        return {"access_token": access_token, "token_type": "bearer"}
