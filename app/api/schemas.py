from datetime import datetime
from typing import Optional, Self

from pydantic import BaseModel, ConfigDict, EmailStr, model_validator

# ==========================
# USER SCHEMAS
# ==========================


# Properties shared across all user actions
class UserBase(BaseModel):
    username: str
    email: EmailStr


# The Request (Create)
class UserCreate(UserBase):
    password: str
    repeat_password: str

    @model_validator(mode="after")
    def passwords_match(self) -> Self:
        if self.password != self.repeat_password:
            raise ValueError("Passwords do not match")
        return self


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(UserBase):
    id: int
    # SQLAlchemy model, not just a standard Python dictionary
    model_config = ConfigDict(from_attributes=True)


# ==========================
# DOCUMENT SCHEMAS
# ==========================


class DocumentBase(BaseModel):
    id: int
    project_id: int
    filename: str
    file_size: int
    created_by: int

    # This tells Pydantic to read the data from the SQLAlchemy database model
    model_config = ConfigDict(from_attributes=True)


class DocumentUpdate(BaseModel):
    filename: str


class DocumentResponse(BaseModel):
    id: int
    filename: str
    file_size: int
    created_by: int

    model_config = ConfigDict(from_attributes=True)


# ==========================
# PROJECT SCHEMAS
# ==========================


class ProjectBase(BaseModel):
    title: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass  # no extra fields for creation


class ProjectResponse(ProjectBase):
    id: int
    created_at: datetime
    created_by: int

    documents: list[DocumentResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class ProjectInvite(BaseModel):
    user_id: int


class ProjectInviteResponse(BaseModel):
    project_id: int
    user_id: int
    role_name: str
