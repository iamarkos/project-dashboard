from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr

# ==========================
# USER SCHEMAS
# ==========================


# 1. The Base: Properties shared across all user actions
class UserBase(BaseModel):
    username: str
    email: EmailStr


# 2. The Request (Create): What we expect the user to send us
class UserCreate(UserBase):
    password: str


# 3. The Response: What we send back to the user
class UserResponse(UserBase):
    id: int
    role_id: int
    # SQLAlchemy model, not just a standard Python dictionary
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

    model_config = ConfigDict(from_attributes=True)


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None


class ProjectInvite(BaseModel):
    user_id: int
    role_id: int


class ProjectInviteResponse(BaseModel):
    project_id: int
    user_id: int
    role_id: int
    role_name: str


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
