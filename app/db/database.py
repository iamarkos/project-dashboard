from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# credentials from our docker-compose.yml
SQLALCHEMY_DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql://dashboard_admin:local_dev_password@127.0.0.1:5433/dashboard_db"
)
# manages the connection pool to PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# individual, temporary database sessions 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# User, Project, Role will inherit from this so SQLAlchemy knows they represent actual db tables
Base = declarative_base() 