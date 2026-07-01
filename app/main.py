from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routers import auth, documents, projects
from app.db.database import Base, SessionLocal, engine
from app.db.models import Role

Base.metadata.create_all(bind=engine)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # This runs once when the app starts
    db = SessionLocal()
    try:
        for role_name in ["Owner", "Participant"]:
            if not db.query(Role).filter(Role.name == role_name).first():
                db.add(Role(name=role_name))
        db.commit()
    finally:
        db.close()
    yield


app = FastAPI(
    title="Project Management Dashboard API",
    description="API for managing projects.",
    lifespan=lifespan,
)

# Plug the router into the main application
app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(documents.router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "success", "message": "API and Database are successfully connected!"}
