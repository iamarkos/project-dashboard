from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
import os

# credentials from our docker-compose.yml
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# app crashes if the .env is missing, rather than failing silently later
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is missing! Check your .env file.")
# manages the connection pool to PostgreSQL
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# individual, temporary database sessions 
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# User, Project, Role will inherit from this so SQLAlchemy knows they represent actual db tables
Base = declarative_base() 