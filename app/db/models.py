from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.db.database import Base


# 1. THE ROLE TABLE
class Role(Base):
    __tablename__ = "roles"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)

    users = relationship("User", back_populates="role")
    # a role can be assigned to many participants across different projects
    participant_assignments = relationship("ProjectParticipant", back_populates="role")


# 2. THE USER TABLE
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    role_id = Column(Integer, ForeignKey("roles.id"))
    role = relationship("Role", back_populates="users")

    # link the user to projects and documents
    owned_projects = relationship("Project", back_populates="owner")
    participating_in = relationship("ProjectParticipant", back_populates="user")


# 3. THE PROJECT TABLE
class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())

    owner = relationship("User", back_populates="owned_projects")

    documents = relationship("Document", back_populates="project", cascade="all, delete-orphan")
    participants = relationship(
        "ProjectParticipant", back_populates="project", cascade="all, delete-orphan"
    )


# 4. THE PROJECT PARTICIPANT TABLE
class ProjectParticipant(Base):
    __tablename__ = "project_participants"

    id = Column(Integer, primary_key=True, index=True)

    project_id = Column(Integer, ForeignKey("projects.id"), index=True)
    user_id = Column(Integer, ForeignKey("users.id"), index=True)
    role_id = Column(Integer, ForeignKey("roles.id"))

    project = relationship("Project", back_populates="participants")
    user = relationship("User", back_populates="participating_in")
    role = relationship("Role", back_populates="participant_assignments")

    __table_args__ = (UniqueConstraint("project_id", "user_id", name="_user_project_uc"),)


# 5. THE DOCUMENT TABLE
class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String)
    file_path = Column(String)
    file_size = Column(Integer)
    project_id = Column(Integer, ForeignKey("projects.id"))
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, server_default=func.now())

    project = relationship("Project", back_populates="documents")
    # no need to access uploader from document
    uploader = relationship("User")
