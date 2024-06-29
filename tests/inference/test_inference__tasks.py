import pytest
import asyncio
from unittest.mock import MagicMock, patch, ANY
from celery.result import AsyncResult
from project.inference.tasks import run_model, task_success_handler
from project.inference.models import ServiceCall
from sqlalchemy import select
from project.inference.model_registry import model_registry
from datetime import datetime, timezone
from tests.factories import ServiceCallFactory
from project.inference.crud import create_service_call
import logging
logger = logging.getLogger(__name__)


import pytest
from unittest.mock import MagicMock, patch
from project.inference.tasks import run_model
from project.inference.model_registry import model_registry

@pytest.mark.asyncio
async def test_run_model_success(db_session, setup_inference_objects, mock_run_model):
    objects = await setup_inference_objects
    model_id = objects['model'].id

    # Define input data
    input_data = {"param1": "value1", "param2": "value2"}

    # Mock Redis client and functions
    with patch('project.redis_utils.redis_client') as mock_redis_client:
        mock_redis_client.get.return_value = None
        mock_redis_client.set.return_value = None

        # Run the task
        result = run_model(model_id, input_data)

        # Assert the task result
        assert result == {"result": "success"}

@pytest.mark.asyncio
async def test_run_model_not_found(db_session, setup_inference_objects):
    non_existent_model_id = 9999

    # Define input data
    input_data = {"param1": "value1", "param2": "value2"}

    # Mock Redis client and functions
    with patch('project.redis_utils.redis_client') as mock_redis_client:
        mock_redis_client.get.return_value = None
        mock_redis_client.set.return_value = None

        # Run the task
        result = run_model(non_existent_model_id, input_data)

        # Assert the task result
        assert result == {"error": f"Model with id {non_existent_model_id} not found"}
        
        
@pytest.mark.asyncio
async def test_task_success_handler():
    # Mock the sender and result
    mock_sender = MagicMock()
    mock_sender.request.id = "mocked_task_id"
    mock_result = {"result": "success"}

    # Mock the update_service_call_time_completed function
    with patch("project.inference.tasks.update_service_call_time_completed", new_callable=MagicMock) as mock_update:
        # Call the success handler
        task_success_handler(sender=mock_sender, result=mock_result)

        # Ensure the update_service_call_time_completed function was called with the correct arguments
        await asyncio.sleep(0.1)  # Give the event loop a chance to run the task
        mock_update.assert_called_once_with(ANY, "mocked_task_id", ANY)
        
        
@pytest.mark.asyncio
async def test_run_model_cache_hit(db_session, setup_inference_objects):
    objects = await setup_inference_objects
    model_id = objects['model'].id

    # Define input data
    input_data = {"param1": "value1", "param2": "value2"}

    # Mock the model function in the registry
    mock_model_func = MagicMock()
    mock_model_func.return_value.Input = MagicMock(return_value=input_data)
    mock_model_func.return_value.predict = MagicMock(return_value={"result": "success"})
    model_registry[model_id]['func'] = mock_model_func

    # Mock Redis client and functions
    cached_result = '{"result": "cached_success"}'.encode('utf-8')
    with patch('project.redis_utils.redis_client') as mock_redis_client:
        mock_redis_client.get.return_value = cached_result
        mock_redis_client.set.return_value = None

        # Run the task
        result = run_model(model_id, input_data)

        # Assert the task result
        assert result == {"result": "cached_success"}

        # Ensure the cache was checked but not set
        cache_key = f"model_{model_id}_result_{hash(frozenset(input_data.items()))}"
        mock_redis_client.get.assert_called_once_with(cache_key)
        mock_redis_client.set.assert_not_called()