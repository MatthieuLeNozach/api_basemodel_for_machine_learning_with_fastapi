import pytest
import logging
from fastapi import Depends
from fastapi.testclient import TestClient
from uuid import uuid4
from sqlalchemy import select
from project.fu_core.users.models import User
from tests.factories import UserFactory, InferenceModelFactory, AccessPolicyFactory, UserAccessFactory
from project.inference import views
from unittest.mock import MagicMock
from project.inference.models import InferenceModel, ServiceCall
from project.inference.ml_models.schemas import TemperatureModelInput

@pytest.fixture
def override_current_active_user():
    def _override_current_active_user(user):
        def override():
            return user
        return override
    return _override_current_active_user
    

@pytest.fixture
def override_unauthorized_user():
    def _override_unauthorized_user():
        return User(id=uuid4(), email="unauthorized@example.com", hashed_password="hashed_password")
    return _override_unauthorized_user
    

@pytest.fixture
def override_current_superuser():
    def _override_current_superuser(user):
        def override():
            return user
        return override
    return _override_current_superuser

@pytest.fixture
def override_current_non_superuser():
    def _override_current_non_superuser():
        return User(id=uuid4(), email="non_superuser@example.com", hashed_password="hashed_password", is_superuser=False)
    return _override_current_non_superuser


@pytest.fixture(autouse=True)
async def clear_db(db_session):
    async with db_session() as session:
        await session.execute("DELETE FROM user")
        await session.commit()

logger = logging.getLogger(__name__)

def test_health_check(client: TestClient):
    response = client.get("/api/v1/inference/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

@pytest.fixture
def temperature_model_input():
    return TemperatureModelInput(
        latitude=40,
        longitude=-74,
        month=6,
        hour=14
    )

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
    
    # Exclude the 'func' key from the comparison
    expected_response = {k: v for k, v in objects['model_registry_entry'].items() if k != 'func'}
    assert response.json() == expected_response



# @pytest.mark.asyncio
# async def test_predict_success(
#     client, 
#     db_session, 
#     mock_run_model, 
#     monkeypatch, 
#     setup_inference_objects, 
#     override_current_active_user
# ):
#     objects = await setup_inference_objects
    
#     # Log the model ID and registry entry
#     logger.info(f"Test Model ID: {objects['model'].id}")
#     logger.info(f"Test Model Registry Entry: {objects['model_registry_entry']}")

#     # Apply the dependency override
#     override = override_current_active_user(objects['user'])
#     client.app.dependency_overrides[views.current_active_user] = override

#     # Mock the model_registry with the correct model ID
#     monkeypatch.setattr(views, "model_registry", {objects['model'].id: objects['model_registry_entry']})

#     # Make the request
#     response = client.get(f"/api/v1/inference/predict/{objects['model'].id}")

#     # Log the response status and content
#     logger.info(f"Response Status Code: {response.status_code}")
#     logger.info(f"Response Content: {response.json()}")

#     assert response.status_code == 200
#     assert "task_id" in response.json()
#     assert response.json()["task_id"] == "mocked_task_id"

#     # Verify that a ServiceCall was created
#     async with db_session() as session:
#         result = await session.execute(
#             select(ServiceCall).where(ServiceCall.model_id == objects['model'].id)
#         )
#         service_call = result.scalar_one_or_none()
#         assert service_call is not None
#         assert service_call.celery_task_id == "mocked_task_id"

#     # Clean up the dependency override
#     client.app.dependency_overrides.clear()
        
        

# @pytest.mark.asyncio
# async def test_predict_unauthorized(
#     client,
#     db_session,
#     mock_run_model,
#     monkeypatch,
#     setup_inference_objects,
#     override_unauthorized_user
# ):
#     objects = await setup_inference_objects
    
#     # Apply the dependency override
#     client.app.dependency_overrides[views.current_active_user] = override_unauthorized_user

#     # Mock the model_registry with the correct model ID
#     monkeypatch.setattr(views, "model_registry", {objects['model'].id: objects['model_registry_entry']})

#     # Make the request
#     response = client.get(f"/api/v1/inference/predict/{objects['model'].id}")
    
#     # Log the response status and content for debugging
#     logger.info(f"Response Status Code: {response.status_code}")
#     logger.info(f"Response Content: {response.json()}")

#     assert response.status_code == 403
#     assert "detail" in response.json()
#     assert "access" in response.json()["detail"].lower()

#     # Clean up the dependency override
#     client.app.dependency_overrides.clear()
    
    
    
# @pytest.mark.asyncio
# async def test_predict_model_not_found(
#     client: TestClient, 
#     db_session, 
#     monkeypatch, 
#     setup_inference_objects, 
#     override_current_active_user
# ):
#     # Use a non-existent model ID
#     non_existent_model_id = 9999

#     # Create a mock user
#     mock_user = User(id=uuid4(), email="test@example.com", hashed_password="hashed_password")

#     # Apply the dependency override
#     client.app.dependency_overrides[views.current_active_user] = override_current_active_user(mock_user)

#     # Mock an empty model_registry
#     monkeypatch.setattr(views, "model_registry", {})

#     # Make the request
#     response = client.get(f"/api/v1/inference/predict/{non_existent_model_id}")

#     # Log the response status and content for debugging
#     logger.info(f"Response Status Code: {response.status_code}")
#     logger.info(f"Response Content: {response.json()}")

#     assert response.status_code == 404
#     assert "detail" in response.json()
#     assert f"Model with id {non_existent_model_id} not found" in response.json()["detail"]

#     # Clean up the dependency override
#     client.app.dependency_overrides.clear()
    


@pytest.mark.asyncio
async def test_task_status(
    client,
    db_session,
    setup_inference_objects,
    mock_run_model,
    monkeypatch,
    override_current_active_user
):
    objects = await setup_inference_objects

    # Apply the dependency override
    override = override_current_active_user(objects['user'])
    client.app.dependency_overrides[views.current_active_user] = override

    # Log the model ID and registry entry
    logger.info(f"Test Model ID: {objects['model'].id}")
    logger.info(f"Test Model Registry Entry: {objects['model_registry_entry']}")

    # Mock the model_registry with the correct model ID
    monkeypatch.setattr(views, "model_registry", {objects['model'].id: objects['model_registry_entry']})

    # Mock the task ID to ensure consistency
    mock_task_id = "mocked_task_id"
    mock_task = MagicMock()
    mock_task.task_id = mock_task_id
    monkeypatch.setattr(views.tasks.run_model, "delay", lambda model_id: mock_task)

    # Create a task
    response = client.get(f"/api/v1/inference/predict/{objects['model'].id}")
    assert response.status_code == 200
    task_id = response.json()["task_id"]

    # Log the task ID
    logger.info(f"Task ID: {task_id}")

    # Ensure the task ID matches the mocked task ID
    assert task_id == mock_task_id

    # Mock the AsyncResult to return a successful state and result
    mock_task.state = "SUCCESS"
    mock_task.result = {"status": "completed"}
    monkeypatch.setattr(views, "AsyncResult", lambda task_id: mock_task)

    # Check the task status
    response = client.get(f"/api/v1/inference/task_status/{task_id}")

    # Log the response status and content for debugging
    logger.info(f"Response Status Code: {response.status_code}")
    logger.info(f"Response Content: {response.json()}")

    assert response.status_code == 200
    


@pytest.mark.asyncio
async def test_pair_user_model_success(client, db_session, override_current_superuser):
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

        # Apply the dependency override for current_superuser
        client.app.dependency_overrides[views.current_superuser] = override_current_superuser(user)

        user_access_data = {
            "user_id": str(uuid4()),
            "model_id": model.id,
            "access_policy_id": access_policy.id
        }

        response = client.post("/api/v1/inference/pair_user_model", json=user_access_data)
        assert response.status_code == 200
        assert response.json()["user_id"] == user_access_data["user_id"]
        assert response.json()["model_id"] == user_access_data["model_id"]
        assert response.json()["access_policy_id"] == user_access_data["access_policy_id"]

        # Clean up the dependency override
        client.app.dependency_overrides.clear()
        
        
        
@pytest.mark.asyncio
async def test_pair_user_model_not_superuser(client, db_session, override_current_superuser):
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

        # Create a non-superuser
        non_superuser = UserFactory.build(is_superuser=False)
        session.add(non_superuser)
        await session.commit()
        await session.refresh(non_superuser)
        mock_user = User(id=uuid4(), email="test@example.com", hashed_password="hashed_password")

        # Apply the dependency override for current_non_superuser
        client.app.dependency_overrides[views.current_superuser] = override_current_superuser(mock_user)

        # Log the user role for debugging
        logger.info(f"User ID: {non_superuser.id}, is_superuser: {non_superuser.is_superuser}")

        user_access_data = {
            "user_id": str(uuid4()),
            "model_id": model.id,
            "access_policy_id": access_policy.id
        }

        response = client.post("/api/v1/inference/pair_user_model", json=user_access_data)
        
        # Log the response status and content for debugging
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Content: {response.json()}")

        assert response.status_code == 403
        assert "detail" in response.json()
        assert "not enough permissions" in response.json()["detail"].lower()

        # Clean up the dependency override
        client.app.dependency_overrides.clear()
        
        
        
@pytest.mark.asyncio
async def test_pair_user_model_model_not_found(client, db_session, override_current_superuser):
    async with db_session() as session:
        # Create necessary objects
        access_policy = AccessPolicyFactory.build()
        session.add(access_policy)
        await session.commit()
        await session.refresh(access_policy)

        user = UserFactory.build(is_superuser=True)
        session.add(user)
        await session.commit()
        await session.refresh(user)

        # Apply the dependency override for current_superuser
        client.app.dependency_overrides[views.current_superuser] = override_current_superuser(user)

        user_access_data = {
            "user_id": str(uuid4()),
            "model_id": 9999,  # Non-existent model ID as an integer
            "access_policy_id": access_policy.id
        }

        response = client.post("/api/v1/inference/pair_user_model", json=user_access_data)
        
        # Log the response status and content for debugging
        logger.info(f"Response Status Code: {response.status_code}")
        logger.info(f"Response Content: {response.json()}")

        assert response.status_code == 404
        assert "detail" in response.json()
        assert "model not found" in response.json()["detail"].lower()

        # Clean up the dependency override
        client.app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_predict_temperature_success(
    client: TestClient,
    db_session,
    mock_run_model,
    monkeypatch,
    setup_inference_objects,
    override_current_active_user,
    temperature_model_input
):
    objects = await setup_inference_objects
    
    # Log the model ID and registry entry
    logger.info(f"Test Model ID: {objects['model'].id}")
    logger.info(f"Test Model Registry Entry: {objects['model_registry_entry']}")

    # Apply the dependency override
    override = override_current_active_user(objects['user'])
    client.app.dependency_overrides[views.current_active_user] = override

    # Mock the model_registry with the correct model ID
    monkeypatch.setattr(views, "model_registry", {objects['model'].id: objects['model_registry_entry']})

    # Make the request
    response = client.post(f"/api/v1/inference/predict-temp/{objects['model'].id}", json=temperature_model_input.dict())

    # Log the response status and content
    logger.info(f"Response Status Code: {response.status_code}")
    logger.info(f"Response Content: {response.json()}")

    assert response.status_code == 200
    assert "task_id" in response.json()
    assert response.json()["task_id"] == "mocked_task_id"

    # Verify that a ServiceCall was created
    async with db_session() as session:
        result = await session.execute(
            select(ServiceCall).where(ServiceCall.model_id == objects['model'].id)
        )
        service_call = result.scalar_one_or_none()
        assert service_call is not None
        assert service_call.celery_task_id == "mocked_task_id"

    # Clean up the dependency override
    client.app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_predict_temperature_model_not_found(
    client: TestClient,
    db_session,
    monkeypatch,
    setup_inference_objects,
    override_current_active_user,
    temperature_model_input
):
    # Use a non-existent model ID
    non_existent_model_id = 9999

    # Create a mock user
    mock_user = User(id=uuid4(), email="test@example.com", hashed_password="hashed_password")

    # Apply the dependency override
    client.app.dependency_overrides[views.current_active_user] = override_current_active_user(mock_user)

    # Mock an empty model_registry
    monkeypatch.setattr(views, "model_registry", {})

    # Make the request
    response = client.post(f"/api/v1/inference/predict-temp/{non_existent_model_id}", json=temperature_model_input.dict())

    # Log the response status and content for debugging
    logger.info(f"Response Status Code: {response.status_code}")
    logger.info(f"Response Content: {response.json()}")

    assert response.status_code == 404
    assert "detail" in response.json()
    assert f"Model with id {non_existent_model_id} not found" in response.json()["detail"]

    # Clean up the dependency override
    client.app.dependency_overrides.clear()

@pytest.mark.asyncio
async def test_predict_temperature_unauthorized(
    client: TestClient,
    db_session,
    mock_run_model,
    monkeypatch,
    setup_inference_objects,
    override_unauthorized_user,
    temperature_model_input
):
    objects = await setup_inference_objects
    
    # Apply the dependency override
    client.app.dependency_overrides[views.current_active_user] = override_unauthorized_user

    # Mock the model_registry with the correct model ID
    monkeypatch.setattr(views, "model_registry", {objects['model'].id: objects['model_registry_entry']})

    # Make the request
    response = client.post(f"/api/v1/inference/predict-temp/{objects['model'].id}", json=temperature_model_input.dict())
    
    # Log the response status and content for debugging
    logger.info(f"Response Status Code: {response.status_code}")
    logger.info(f"Response Content: {response.json()}")

    assert response.status_code == 403
    assert "detail" in response.json()
    assert "access" in response.json()["detail"].lower()

    # Clean up the dependency override
    client.app.dependency_overrides.clear()