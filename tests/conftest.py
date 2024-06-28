import os
import pytest
from pytest_factoryboy import register
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from alembic.config import Config
from alembic import command
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set the environment variable to use the testing configuration
os.environ["FASTAPI_CONFIG"] = "testing"

from project.config import settings as _settings
from project.database import Base, engine, async_session_maker
from project import create_app
from tests.factories import (
    UserFactory,
    AccessPolicyFactory,
    InferenceModelFactory,
    UserAccessFactory,
    ServiceCallFactory
)

# Register the factories
register(UserFactory)
register(AccessPolicyFactory)
register(InferenceModelFactory)
register(UserAccessFactory)
register(ServiceCallFactory)

@pytest.fixture()
def settings():
    # Log the DATABASE_URL
    logger.info("\n\nDATABASE_URL: %s\n", _settings.DATABASE_URL)
    return _settings

@pytest.fixture()
def app(settings):
    app = create_app()
    return app



@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Apply Alembic migrations at the beginning of the test session."""
    db_path = "./test.db"
    
    # Delete the existing database file if it exists
    if os.path.exists(db_path):
        os.remove(db_path)
        logger.info(f"Deleted existing database file at {db_path}")

    # Create a new database and apply migrations
    alembic_cfg = Config("alembic.ini")
    logger.info("Starting Alembic migrations")
    command.upgrade(alembic_cfg, "head")
    logger.info("Finished Alembic migrations")
    
    yield
    
    # The database file will remain after the tests for inspection

    

@pytest.fixture
def db_session():
    return async_session_maker


@pytest.fixture()
def client(app):
    with TestClient(app) as client:
        yield client