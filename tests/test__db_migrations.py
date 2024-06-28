import pytest
from sqlalchemy import text
from project.fu_core.users.models import User
from project.inference.models import AccessPolicy, InferenceModel, UserAccess, ServiceCall

@pytest.mark.asyncio
async def test_database_tables_exist(db_session):
    async with db_session() as session:
        # Check if tables exist
        tables = ['user', 'access_policy', 'inference_model', 'user_access', 'service_call']
        for table in tables:
            result = await session.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"))
            assert result.scalar() is not None, f"Table {table} does not exist"