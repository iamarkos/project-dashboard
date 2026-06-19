from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime

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