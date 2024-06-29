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

@pytest.mark.asyncio
async def test_user_table_structure(db_session):
    async with db_session() as session:
        result = await session.execute(text("PRAGMA table_info(user)"))
        columns = result.fetchall()
        column_names = [col[1] for col in columns]
        assert set(column_names) == {'id', 'email', 'hashed_password', 'is_active', 'is_superuser', 'is_verified', 'date_created', 'date_deleted'}

