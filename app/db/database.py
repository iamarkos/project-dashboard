from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

# credentials from our docker-compose.yml
SQLALCHEMY_DATABASE_URL = f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@db:5432/{settings.POSTGRES_DB}"
# manages the connection pool to PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# individual, temporary database sessions
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# User, Project, Role will inherit from this so SQLAlchemy knows they represent actual db tables
class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
