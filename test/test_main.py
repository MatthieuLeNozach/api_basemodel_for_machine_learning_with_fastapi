
from fastapi.testclient import TestClient
import pytest
from sqlalchemy.orm import Session
from ..app.main import app, startup_event, shutdown_event
from ..app.models import User
from ..app.database import SessionLocal

from ..app import main

from fastapi import status


client = TestClient(main.app)


def test_return_health_check():
    response = client.get('/healthcheck')
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {'status': 'healthy'}
    
    
@pytest.fixture(scope="function")
def db_session():
    # Create a new database session for the test
    db = SessionLocal()
    try:
        yield db
    finally:
        # Clean up the test database after the test is done
        db.close()

@pytest.mark.asyncio
async def test_startup_creates_superuser(monkeypatch, db_session: Session):
    # Set the environment variable to create a superuser
    monkeypatch.setenv('CREATE_SUPERUSER', 'True')

    # Call the startup event directly
    await startup_event()

    # Check if the superuser was created
    superuser = db_session.query(User).filter_by(username='superuser@example.com').first()
    assert superuser is not None
    assert superuser.role == 'admin'

    # Clean up by calling the shutdown event directly
    await shutdown_event()

    # Check if the superuser was removed
    superuser = db_session.query(User).filter_by(username='superuser@example.com').first()
    assert superuser is None