from datetime import datetime

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.database import Base


# 1. THE ROLE TABLE
class Role(Base):
    __tablename__ = "roles"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(unique=True, index=True)

    # A role can be assigned to many participants across different projects
    participant_assignments: Mapped[list["ProjectParticipant"]] = relationship(
        back_populates="role"
    )


# 2. THE USER TABLE
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    username: Mapped[str] = mapped_column(unique=True, index=True)
    email: Mapped[str] = mapped_column(unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column()

    # Link the user to projects
    participating_in: Mapped[list["ProjectParticipant"]] = relationship(back_populates="user")


# 3. THE PROJECT TABLE
class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(index=True)
    # Using str | None makes it nullable in the DB
    description: Mapped[str | None] = mapped_column()
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    documents: Mapped[list["Document"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
    participants: Mapped[list["ProjectParticipant"]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )


# 4. THE PROJECT PARTICIPANT TABLE
class ProjectParticipant(Base):
    __tablename__ = "project_participants"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    role_id: Mapped[int] = mapped_column(ForeignKey("roles.id"))

    project: Mapped["Project"] = relationship(back_populates="participants")
    user: Mapped["User"] = relationship(back_populates="participating_in")
    role: Mapped["Role"] = relationship(back_populates="participant_assignments")

    __table_args__ = (UniqueConstraint("project_id", "user_id", name="_user_project_uc"),)


# 5. THE DOCUMENT TABLE
class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    filename: Mapped[str] = mapped_column()
    file_path: Mapped[str] = mapped_column()
    file_size: Mapped[int] = mapped_column()
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"))
    created_by: Mapped[int] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())

    project: Mapped["Project"] = relationship(back_populates="documents")
    uploader: Mapped["User"] = relationship()
