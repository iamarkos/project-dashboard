from fastapi import FastAPI
from app.db.database import engine, Base
from app.models import models

# Import your new router
from app.routers import users, auth, projects

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Project Management Dashboard API",
    description="API for managing projects."
)

# Plug the router into the main application
app.include_router(users.router)
app.include_router(auth.router)
app.include_router(projects.router)

@app.get("/")
def read_root():
    return {"status": "success", "message": "API and Database are successfully connected!"}