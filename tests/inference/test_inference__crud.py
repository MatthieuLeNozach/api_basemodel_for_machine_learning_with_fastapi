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
        # Create AccessPolicy first
        access_policy = AccessPolicyFactory.build()
        session.add(access_policy)
        await session.commit()
        await session.refresh(access_policy)

        # Now create InferenceModel
        model = InferenceModelFactory.build(access_policy_id=access_policy.id)
        session.add(model)
        await session.commit()
        await session.refresh(model)

        # Test getting the model
        retrieved_model = await crud.get_inference_model(session, model.id)
        assert retrieved_model is not None
        assert retrieved_model.id == model.id
        assert retrieved_model.name == model.name
        assert retrieved_model.access_policy_id == access_policy.id
        
        

@pytest.mark.asyncio
async def test_create_user_access(db_session):
    async with db_session() as session:
        # Create AccessPolicy first
        access_policy = AccessPolicyFactory.build()
        session.add(access_policy)
        await session.commit()
        await session.refresh(access_policy)

        # Now create InferenceModel
        model = InferenceModelFactory.build(access_policy_id=access_policy.id)
        session.add(model)
        await session.commit()
        await session.refresh(model)

        # Create User
        user = UserFactory.build()
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Now create UserAccess
        user_access = await crud.create_user_access(
            session,
            user_id=user.id,
            model_id=model.id,
            access_policy_id=access_policy.id
        )

        assert user_access is not None
        assert user_access.user_id == user.id
        assert user_access.model_id == model.id
        assert user_access.access_policy_id == access_policy.id
        
        

@pytest.mark.asyncio
async def test_get_user_access(db_session):
    async with db_session() as session:
        # Create AccessPolicy
        access_policy = AccessPolicyFactory.build()
        session.add(access_policy)
        await session.commit()
        await session.refresh(access_policy)

        # Create InferenceModel
        model = InferenceModelFactory.build(access_policy_id=access_policy.id)
        session.add(model)
        await session.commit()
        await session.refresh(model)

        # Create UserAccess
        user_access = UserAccessFactory.build(
            model_id=model.id,
            access_policy_id=access_policy.id
        )
        session.add(user_access)
        await session.commit()
        await session.refresh(user_access)

        # Test getting the user access
        retrieved_user_access = await crud.get_user_access(session, user_access.user_id, model.id)
        assert retrieved_user_access is not None
        assert retrieved_user_access.user_id == user_access.user_id
        assert retrieved_user_access.model_id == model.id
        assert retrieved_user_access.access_policy_id == access_policy.id
        
        

@pytest.mark.asyncio
async def test_create_service_call(db_session):
    async with db_session() as session:
        # Create AccessPolicy
        access_policy = AccessPolicyFactory.build()
        session.add(access_policy)
        await session.commit()
        await session.refresh(access_policy)

        # Create InferenceModel
        model = InferenceModelFactory.build(access_policy_id=access_policy.id)
        session.add(model)
        await session.commit()
        await session.refresh(model)

        # Create User
        user = UserFactory.build()
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Create ServiceCall
        service_call = await crud.create_service_call(session, model.id, user.id, "test_task_id")
        assert service_call.model_id == model.id
        assert service_call.user_id == user.id
        assert service_call.celery_task_id == "test_task_id"
        
        

@pytest.mark.asyncio
async def test_check_user_access_and_update(db_session):
    async with db_session() as session:
        # Create AccessPolicy
        policy = AccessPolicyFactory.build(daily_api_calls=10, monthly_api_calls=100)
        session.add(policy)
        await session.commit()
        await session.refresh(policy)

        # Create InferenceModel
        model = InferenceModelFactory.build(access_policy_id=policy.id)
        session.add(model)
        await session.commit()
        await session.refresh(model)

        # Create User
        user = UserFactory.build()
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Create UserAccess
        user_access = UserAccessFactory.build(
            user_id=user.id,
            model_id=model.id,
            access_policy_id=policy.id
        )
        session.add(user_access)
        await session.commit()
        await session.refresh(user_access)

        access_granted, message = await crud.check_user_access_and_update(session, user.id, model.id)
        assert access_granted is True
        assert message == "Access granted"

        # Test exceeding daily limit
        for _ in range(10):
            service_call = ServiceCallFactory.build(user_id=user.id, model_id=model.id)
            session.add(service_call)
        await session.commit()
        
        access_granted, message = await crud.check_user_access_and_update(session, user.id, model.id)
        assert access_granted is False
        assert message == "Daily API call limit exceeded"