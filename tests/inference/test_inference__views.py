import pytest
import logging
from fastapi.testclient import TestClient
from uuid import uuid4
from tests.factories import UserFactory, InferenceModelFactory, AccessPolicyFactory, UserAccessFactory
from project.inference import views
from project.inference.models import InferenceModel, ServiceCall

logger = logging.getLogger(__name__)

def test_health_check(client: TestClient):
    response = client.get("/api/v1/inference/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.mark.asyncio
async def test_get_model_info(client: TestClient, db_session, setup_inference_objects):
    objects = await setup_inference_objects
    
    # Log the model ID and registry entry
    logger.info(f"Test Model ID: {objects['model'].id}")
    logger.info(f"Test Model Registry Entry: {objects['model_registry_entry']}")

    # Make the request
    response = client.get(f"/api/v1/inference/predict/get_info/{objects['model'].id}")
    
    # Log the response status and content
    logger.info(f"Response Status Code: {response.status_code}")
    logger.info(f"Response Content: {response.json()}")

    assert response.status_code == 200
    assert response.json() == objects['model_registry_entry']



@pytest.mark.asyncio
async def test_predict(client: TestClient, db_session, mock_user, mock_run_model, monkeypatch, setup_inference_objects):
    objects = await setup_inference_objects
    
    # Log the model ID and registry entry
    logger.info(f"Test Model ID: {objects['model'].id}")
    logger.info(f"Test Model Registry Entry: {objects['model_registry_entry']}")

    # Mock the current_active_user dependency
    monkeypatch.setattr(views, "current_active_user", lambda: mock_user)

    # Mock the model_registry with the correct model ID
    monkeypatch.setattr(views, "model_registry", {objects['model'].id: objects['model_registry_entry']})

    # Make the request
    response = client.get(f"/api/v1/inference/predict/{objects['model'].id}")
    
    # Log the response status and content
    logger.info(f"Response Status Code: {response.status_code}")
    logger.info(f"Response Content: {response.json()}")

    assert response.status_code == 200
    assert "task_id" in response.json()
    assert response.json()["task_id"] == "mocked_task_id"

    # Verify that a ServiceCall was created
    async with db_session() as session:
        service_call = await session.execute(ServiceCall.select().where(ServiceCall.model_id == objects['model'].id))
        service_call = service_call.scalar_one_or_none()
        assert service_call is not None
        assert service_call.celery_task_id == "mocked_task_id"


@pytest.mark.asyncio
async def test_predict_model_not_found(client):
    response = await client.get("/predict/9999")
    assert response.status_code == 404

@pytest.mark.asyncio
async def test_task_status(client):
    # Assuming you have a way to create a task and get its ID
    task_id = "some_task_id"
    response = await client.get(f"/task_status/{task_id}")
    assert response.status_code == 200
    assert "state" in response.json()

@pytest.mark.asyncio
async def test_pair_user_model(client, db_session):
    async with db_session() as session:
        # Create necessary objects
        access_policy = AccessPolicyFactory.build()
        session.add(access_policy)
        await session.commit()
        await session.refresh(access_policy)

        model = InferenceModelFactory.build(access_policy_id=access_policy.id)
        session.add(model)
        await session.commit()
        await session.refresh(model)

        user = UserFactory.build(is_superuser=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Authenticate the superuser (you might need to implement this)
        # client.auth_token = get_auth_token(user)

        user_access_data = {
            "user_id": str(uuid4()),
            "model_id": model.id,
            "access_policy_id": access_policy.id
        }

        response = await client.post("/pair_user_model", json=user_access_data)
        assert response.status_code == 200
        assert response.json()["user_id"] == user_access_data["user_id"]
        assert response.json()["model_id"] == user_access_data["model_id"]
        assert response.json()["access_policy_id"] == user_access_data["access_policy_id"]

# Add more test cases as needed