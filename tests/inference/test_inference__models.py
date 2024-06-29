# /tests/inference/test_inference_crud.py

import pytest
from uuid import uuid4
from project.inference import crud
from tests.factories import AccessPolicyFactory, InferenceModelFactory, UserFactory, UserAccessFactory, ServiceCallFactory

@pytest.mark.asyncio
async def test_create_access_policy(db_session):
    async with db_session() as session:
        policy = await crud.create_access_policy(session, "test_policy", 100, 3000)
        assert policy.name == "test_policy"
        assert policy.daily_api_calls == 100
        assert policy.monthly_api_calls == 3000

@pytest.mark.asyncio
async def test_get_access_policy_by_name(db_session):
    async with db_session() as session:
        policy = AccessPolicyFactory.build()
        session.add(policy)
        await session.commit()
        
        retrieved_policy = await crud.get_access_policy_by_name(session, policy.name)
        assert retrieved_policy is not None
        assert retrieved_policy.name == policy.name

@pytest.mark.asyncio
async def test_create_inference_model(db_session):
    async with db_session() as session:
        policy = AccessPolicyFactory.build()
        session.add(policy)
        await session.commit()
        
        model = await crud.create_inference_model(
            session, 
            name="test_model", 
            access_policy_id=policy.id, 
            problem="classification",
            category="test",
            version="1.0.0"
        )
        assert model.name == "test_model"
        assert model.access_policy_id == policy.id

@pytest.mark.asyncio
async def test_get_inference_model(db_session):
    async with db_session() as session:
        model = InferenceModelFactory.build()
        session.add(model)
        await session.commit()
        
        retrieved_model = await crud.get_inference_model(session, model.id)
        assert retrieved_model is not None
        assert retrieved_model.id == model.id

@pytest.mark.asyncio
async def test_create_user_access(db_session):
    async with db_session() as session:
        user = UserFactory.build()
        model = InferenceModelFactory.build()
        policy = AccessPolicyFactory.build()
        session.add_all([user, model, policy])
        await session.commit()
        
        user_access = await crud.create_user_access(session, user.id, model.id, policy.id)
        assert user_access.user_id == user.id
        assert user_access.model_id == model.id
        assert user_access.access_policy_id == policy.id

@pytest.mark.asyncio
async def test_get_user_access(db_session):
    async with db_session() as session:
        # Set the session for all factories
        UserAccessFactory._meta.sqlalchemy_session = session
        InferenceModelFactory._meta.sqlalchemy_session = session
        AccessPolicyFactory._meta.sqlalchemy_session = session

        # Create AccessPolicy first
        access_policy = AccessPolicyFactory()
        await session.flush()

        # Create InferenceModel
        inference_model = InferenceModelFactory(access_policy_id=access_policy.id)
        await session.flush()

        # Create UserAccess
        user_access = UserAccessFactory(model_id=inference_model.id, access_policy_id=access_policy.id)
        await session.commit()

        # Test get_user_access
        retrieved_access = await crud.get_user_access(session, user_access.user_id, user_access.model_id)
        assert retrieved_access is not None
        assert retrieved_access.user_id == user_access.user_id
        assert retrieved_access.model_id == user_access.model_id

        # Reset the session for all factories
        UserAccessFactory._meta.sqlalchemy_session = None
        InferenceModelFactory._meta.sqlalchemy_session = None
        AccessPolicyFactory._meta.sqlalchemy_session = None
        
        

@pytest.mark.asyncio
async def test_create_service_call(db_session):
    async with db_session() as session:
        model = InferenceModelFactory.build()
        user = UserFactory.build()
        session.add_all([model, user])
        await session.commit()
        
        service_call = await crud.create_service_call(session, model.id, user.id, "test_task_id")
        assert service_call.model_id == model.id
        assert service_call.user_id == user.id
        assert service_call.celery_task_id == "test_task_id"

@pytest.mark.asyncio
async def test_check_user_access_and_update(db_session):
    async with db_session() as session:
        # Set the session for all factories
        UserFactory._meta.sqlalchemy_session = session
        AccessPolicyFactory._meta.sqlalchemy_session = session
        InferenceModelFactory._meta.sqlalchemy_session = session
        UserAccessFactory._meta.sqlalchemy_session = session
        ServiceCallFactory._meta.sqlalchemy_session = session

        # Create AccessPolicy first
        policy = AccessPolicyFactory(daily_api_calls=10, monthly_api_calls=100)
        await session.flush()

        # Create InferenceModel
        model = InferenceModelFactory(access_policy_id=policy.id)
        await session.flush()

        # Create User
        user = UserFactory()
        await session.flush()

        # Create UserAccess
        user_access = UserAccessFactory(user_id=user.id, model_id=model.id, access_policy_id=policy.id)
        await session.commit()

        # Test check_user_access_and_update
        access_granted, message = await crud.check_user_access_and_update(session, user.id, model.id)
        assert access_granted is True
        assert message == "Access granted"

        # Test exceeding daily limit
        for _ in range(10):
            service_call = ServiceCallFactory(user_id=user.id, model_id=model.id)
            session.add(service_call)
        await session.commit()

        access_granted, message = await crud.check_user_access_and_update(session, user.id, model.id)
        assert access_granted is False
        assert message == "Daily API call limit exceeded"

        # Reset the session for all factories
        UserFactory._meta.sqlalchemy_session = None
        AccessPolicyFactory._meta.sqlalchemy_session = None
        InferenceModelFactory._meta.sqlalchemy_session = None
        UserAccessFactory._meta.sqlalchemy_session = None
        ServiceCallFactory._meta.sqlalchemy_session = None