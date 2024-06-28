import os
import pytest
from pytest_factoryboy import register
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession
from alembic.config import Config
from alembic import command

# Import models to ensure they are registered with SQLAlchemy
from project.fu_core.users.models import User
from project.inference.models import (
    UserAccess,
    ServiceCall,
    InferenceModel,
    AccessPolicy
)

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
    return _settings

@pytest.fixture()
def app(settings):
    app = create_app()
    return app

@pytest.fixture(scope="session", autouse=True)
def apply_migrations():
    """Apply Alembic migrations at the beginning of the test session."""
    alembic_cfg = Config("alembic.ini")
    command.upgrade(alembic_cfg, "head")
    yield
    command.downgrade(alembic_cfg, "base")

@pytest.fixture()
async def db_session(app):
    async_session = async_session_maker()
    async with async_session() as session:
        yield session

@pytest.fixture()
def client(app):
    with TestClient(app) as client:
        yield client