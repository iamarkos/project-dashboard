from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routers import auth, documents, projects
from app.db.database import Base, SessionLocal, engine
from app.db.models import Role


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # 1. Create all tables in the database (replaces Alembic)
    Base.metadata.create_all(bind=engine)

    # 2. Seed the required roles into the newly created tables
    db = SessionLocal()
    try:
        for role_name in ["Owner", "Participant"]:
            if not db.query(Role).filter(Role.name == role_name).first():
                db.add(Role(name=role_name))
        db.commit()
    finally:
        db.close()

    yield


def register_middlewares(app: FastAPI) -> None:
    """Register all middlewares."""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def register_routers(app: FastAPI) -> None:
    """
    Register all routers.
    """
    app.include_router(auth.router)
    app.include_router(projects.router, prefix="/projects")
    app.include_router(documents.router, prefix="/projects/{project_id}/documents")


def create_app() -> FastAPI:
    """Main application factory."""

    app = FastAPI(title="Project Management API", version="1.0.0", lifespan=lifespan)

    # Call the register functions
    register_middlewares(app)
    register_routers(app)

    return app


app = create_app()
