import pytest
from sqlalchemy import text
from project.fu_core.users.models import User
from project.inference.models import AccessPolicy, InferenceModel, UserAccess, ServiceCall


@pytest.mark.asyncio
async def test_access_policy_table_structure(db_session):
    async with db_session() as session:
        result = await session.execute(text("PRAGMA table_info(access_policy)"))
        columns = result.fetchall()
        column_names = [col[1] for col in columns]
        assert set(column_names) == {'id', 'name', 'daily_api_calls', 'monthly_api_calls'}

@pytest.mark.asyncio
async def test_inference_model_table_structure(db_session):
    async with db_session() as session:
        result = await session.execute(text("PRAGMA table_info(inference_model)"))
        columns = result.fetchall()
        column_names = [col[1] for col in columns]
        assert set(column_names) == {'id', 'name', 'problem', 'category', 'version', 'first_deployed', 'last_updated', 'deployment_status', 'in_production', 'mlflow_id', 'source_url', 'access_policy_id'}

@pytest.mark.asyncio
async def test_user_access_table_structure(db_session):
    async with db_session() as session:
        result = await session.execute(text("PRAGMA table_info(user_access)"))
        columns = result.fetchall()
        column_names = [col[1] for col in columns]
        assert set(column_names) == {'user_id', 'model_id', 'access_policy_id', 'api_calls', 'access_granted', 'last_accessed'}

@pytest.mark.asyncio
async def test_service_call_table_structure(db_session):
    async with db_session() as session:
        result = await session.execute(text("PRAGMA table_info(service_call)"))
        columns = result.fetchall()
        column_names = [col[1] for col in columns]
        assert set(column_names) == {'id', 'model_id', 'user_id', 'time_requested', 'time_completed', 'celery_task_id'}

@pytest.mark.asyncio
async def test_foreign_key_relationships(db_session):
    async with db_session() as session:
        # Check foreign keys for inference_model
        result = await session.execute(text("PRAGMA foreign_key_list(inference_model)"))
        fks = result.fetchall()
        assert any(fk[2] == 'access_policy' for fk in fks)

        # Check foreign keys for user_access
        result = await session.execute(text("PRAGMA foreign_key_list(user_access)"))
        fks = result.fetchall()
        assert any(fk[2] == 'user' for fk in fks)
        assert any(fk[2] == 'inference_model' for fk in fks)
        assert any(fk[2] == 'access_policy' for fk in fks)

        # Check foreign keys for service_call
        result = await session.execute(text("PRAGMA foreign_key_list(service_call)"))
        fks = result.fetchall()
        assert any(fk[2] == 'inference_model' for fk in fks)
        assert any(fk[2] == 'user' for fk in fks)

@pytest.mark.asyncio
async def test_indexes(db_session):
    async with db_session() as session:
        # Check indexes for user table
        result = await session.execute(text("PRAGMA index_list(user)"))
        indexes = result.fetchall()
        assert any(idx[1] == 'ix_user_email' for idx in indexes)

        # Check indexes for access_policy table
        result = await session.execute(text("PRAGMA index_list(access_policy)"))
        indexes = result.fetchall()
        assert any(idx[1] == 'ix_access_policy_id' for idx in indexes)

        # Check indexes for inference_model table
        result = await session.execute(text("PRAGMA index_list(inference_model)"))
        indexes = result.fetchall()
        assert any(idx[1] == 'ix_inference_model_id' for idx in indexes)

        # Check indexes for service_call table
        result = await session.execute(text("PRAGMA index_list(service_call)"))
        indexes = result.fetchall()
        assert any(idx[1] == 'ix_service_call_id' for idx in indexes)