import pytest
from sqlalchemy import StaticPool
from sqlmodel import create_engine, SQLModel, Session
from fastapi.testclient import TestClient

from db import get_session
from server import app



@pytest.fixture(scope="session")
def test_engine():
    """Create a shared in-memory SQLite engine for the test session"""
    engine = create_engine("sqlite:///:memory:", poolclass=StaticPool, connect_args={"check_same_thread": False})
    SQLModel.metadata.create_all(engine)
    return engine

@pytest.fixture(autouse=True)
def clean_tables(test_engine):
    SQLModel.metadata.drop_all(test_engine)
    SQLModel.metadata.create_all(test_engine)

@pytest.fixture(scope="function")
def test_session(test_engine):
    """Create a new session for each test function and seed test data"""
    with Session(test_engine) as session:
        yield session


@pytest.fixture(scope="function")
def client(test_session):
    """Override FastAPI session dependency with test session"""
    def override_get_session():
        yield test_session

    app.dependency_overrides[get_session] = override_get_session
    yield TestClient(app)
    app.dependency_overrides.clear()