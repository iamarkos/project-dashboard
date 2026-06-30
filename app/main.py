from fastapi import FastAPI

# Import your new router
from app.api import auth, projects
from app.db.database import Base, engine

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Project Management Dashboard API", description="API for managing projects.")

# Plug the router into the main application
app.include_router(auth.router)
app.include_router(projects.router)


@app.get("/")
def read_root() -> dict[str, str]:
    return {"status": "success", "message": "API and Database are successfully connected!"}
