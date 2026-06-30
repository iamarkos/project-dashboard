import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import database
from app.main import app
from app.api.dependencies import get_db
from app.db.database import Base
from app.core.config import settings  # Import your existing settings!

# Use the secure URL from your environment variables
engine = create_engine(database.SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    # Create the tables once for the test session
    Base.metadata.create_all(bind=engine)
    yield
    # Drop them after all tests are done
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session():
    # Connect to the database
    connection = engine.connect()
    # Begin a non-ORM transaction
    transaction = connection.begin()
    # Bind an individual Session to the connection
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    # Close the session and roll back everything
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="function")
def client(db_session):
    # Override the get_db dependency to use our testing session
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    # Clear overrides after the test
    app.dependency_overrides.clear()