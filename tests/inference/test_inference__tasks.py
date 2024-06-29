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


@pytest.mark.asyncio
async def test_run_model_success(db_session, setup_inference_objects, mock_run_model):
    objects = await setup_inference_objects
    model_id = objects['model'].id

    # Mock the model function in the registry
    mock_model_func = MagicMock(return_value={"result": "success"})
    model_registry[model_id]['func'] = mock_model_func

    # Run the task
    result = run_model(model_id)

    # Assert the task result
    assert result == {"result": "success"}

@pytest.mark.asyncio
async def test_run_model_not_found(db_session, setup_inference_objects):
    non_existent_model_id = 9999

    # Run the task
    result = run_model(non_existent_model_id)

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