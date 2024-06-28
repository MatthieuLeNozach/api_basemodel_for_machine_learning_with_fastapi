import os
import pytest
from pytest_factoryboy import register
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

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

@pytest.fixture()
async def db_session(app):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = async_session_maker()
    async with async_session() as session:
        yield session
        
    async with engine.begin() as conn:
        await conn.run_sync(conn.run_sync(Base.metadata.drop_all))
        
@pytest.fixture()
def client(app):
    with TestClient(app) as client:
        yield client