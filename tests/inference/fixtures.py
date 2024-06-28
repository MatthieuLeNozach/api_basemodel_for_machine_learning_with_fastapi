import pytest
from project.inference.models import AccessPolicy, InferenceModel, UserAccess
from project.fu_core.users.models import User
from uuid import uuid4

@pytest.fixture()
def mock_run_model(monkeypatch, mock_celery_task):
    def mock_delay(model_id):
        return mock_celery_task

    from project.inference import views
    monkeypatch.setattr(views.tasks.run_model, "delay", mock_delay)
    return mock_delay


import logging
from project.inference.model_registry import model_registry

logger = logging.getLogger(__name__)

@pytest.fixture
async def setup_inference_objects(db_session):
    async with db_session() as session:
        # Create AccessPolicy
        access_policy = AccessPolicy(name="Test Policy", daily_api_calls=100, monthly_api_calls=3000)
        session.add(access_policy)
        await session.commit()
        await session.refresh(access_policy)

        # Create InferenceModel
        model = InferenceModel(
            name="Test Model", 
            access_policy_id=access_policy.id,
            problem="classification",
            category="test",
            version="1.0.0"
        )
        session.add(model)
        await session.commit()
        await session.refresh(model)

        # Create User
        user = User(id=uuid4(), email="test@example.com", hashed_password="hashed_password")
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Create UserAccess
        user_access = UserAccess(
            user_id=user.id,
            model_id=model.id,
            access_policy_id=access_policy.id
        )
        session.add(user_access)
        await session.commit()
        await session.refresh(user_access)

        # Update the model_registry with the created model
        model_registry_entry = {
            "name": model.name,
            "problem": model.problem,
            "category": model.category,
            "version": model.version,
            "access_policy_id": model.access_policy_id
        }
        model_registry[model.id] = model_registry_entry

        # Log the model ID and registry entry
        logger.info(f"Model ID: {model.id}")
        logger.info(f"Model Registry Entry: {model_registry_entry}")

        return {
            "access_policy": access_policy,
            "model": model,
            "user": user,
            "user_access": user_access,
            "model_registry_entry": model_registry_entry
        }