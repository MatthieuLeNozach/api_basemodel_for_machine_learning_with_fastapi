
import pytest
from project.inference.models import AccessPolicy, InferenceModel, UserAccess
from project.fu_core.users.models import User
from uuid import uuid4
from tests.factories import AccessPolicyFactory, InferenceModelFactory, UserFactory, UserAccessFactory

import logging
from project.inference.model_registry import model_registry

logger = logging.getLogger(__name__)


@pytest.fixture()
def mock_run_model(monkeypatch, mock_celery_task):
    def mock_delay(model_id):
        return mock_celery_task

    from project.inference import views
    monkeypatch.setattr(views.tasks.run_model, "delay", mock_delay)
    return mock_delay

@pytest.fixture
async def setup_inference_objects(db_session):
    async with db_session() as session:
        # Set the session for all factories
        AccessPolicyFactory._meta.sqlalchemy_session = session
        InferenceModelFactory._meta.sqlalchemy_session = session
        UserFactory._meta.sqlalchemy_session = session
        UserAccessFactory._meta.sqlalchemy_session = session

        # Create AccessPolicy
        access_policy = AccessPolicyFactory()
        await session.flush()

        # Create InferenceModel
        model = InferenceModelFactory(
            access_policy_id=access_policy.id,
            problem="classification",
            category="test",
            version="1.0.0"
        )
        await session.flush()

        # Create User
        user = UserFactory()
        await session.flush()

        # Create UserAccess
        user_access = UserAccessFactory(
            user_id=user.id,
            model_id=model.id,
            access_policy_id=access_policy.id
        )
        await session.flush()

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

        await session.commit()

        return {
            "access_policy": access_policy,
            "model": model,
            "user": user,
            "user_access": user_access,
            "model_registry_entry": model_registry_entry
        }