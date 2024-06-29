import asyncio
from celery.result import AsyncResult
from celery import shared_task
from project.celery_utils import custom_celery_task
from celery.signals import task_failure, task_success
from project.inference.model_registry import model_registry
from project.database import get_async_session
from project.inference.crud import update_service_call_time_completed
from datetime import datetime
import logging
logger = logging.getLogger(__name__)

@shared_task
def run_regression():
    import numpy as np
    from sklearn.linear_model import LinearRegression
    from sklearn.datasets import make_regression

    #model_specs = 
    # Generate synthetic dataset with only numeric features
    X, y = make_regression(n_samples=100, n_features=3, noise=0.1)
    
    # Create and fit the model
    model = LinearRegression()
    model.fit(X, y)
    
    # Make predictions
    predictions = model.predict(X)
    
    return predictions.tolist()

# Base task with @shared_task
#@shared_task
# def run_model(model_id: int):
#     if model_id not in model_registry:
#         return {"error": f"Model with id {model_id} not found"}
    
#     model_info = model_registry[model_id]
#     model_func = model_info['func']
#     return model_func()


@custom_celery_task(bind=True, max_retries=3, retry_backoff=True)
def run_model(self, model_id: int):
    if model_id not in model_registry:
        logger.error(f"Model with id {model_id} not found")
        return {"error": f"Model with id {model_id} not found"}
    
    model_func = model_registry[model_id]['func']
    try:
        result = model_func()
        logger.info(f"Model {model_id} executed successfully with result: {result}")
        return result
    except Exception as e:
        logger.error(f"Error executing model {model_id}: {e}")
        raise self.retry(exc=e)

# @shared_task
# def run_model(model_id: int):
#     if model_id not in model_registry:
#         return {"error": f"Model with id {model_id} not found"}
    
#     model_func = model_registry[model_id]['model_func']
#     return model_func()


# @task_success.connect(sender=run_model)
# def task_success_handler(sender, result, **kwargs):
#     task_id = sender.request.id
#     task_result = AsyncResult(task_id)
#     time_completed = task_result.date_done

#     async def update_task():
#         async for session in get_async_session():
#             await update_service_call_time_completed(session, task_id, time_completed)
    
#     asyncio.run(update_task())
  
    
@task_success.connect(sender=run_model)
def task_success_handler(sender, result, **kwargs):
    task_id = sender.request.id
    task_result = AsyncResult(task_id)
    time_completed = task_result.date_done

    async def update_task():
        async for session in get_async_session():
            await update_service_call_time_completed(session, task_id, time_completed)
    
    # Check if there's an existing event loop
    if asyncio.get_event_loop().is_running():
        # If there's an existing event loop, create a task
        asyncio.create_task(update_task())
    else:
        # Otherwise, run the coroutine
        asyncio.run(update_task())

