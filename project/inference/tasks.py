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
import json
from project.redis_utils import get_cache, set_cache
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
def run_model(self, model_id: int, input_data: dict):
    logger.info(f"Running model with id {model_id}")
    if model_id not in model_registry:
        logger.error(f"Model with id {model_id} not found")
        return {"error": f"Model with id {model_id} not found"}
    
    model_func = model_registry[model_id]['func']
    model = model_func()
    
    # Generate a cache key based on model_id and input parameters
    cache_key = f"model_{model_id}_result_{hash(frozenset(input_data.items()))}"
    logger.info(f"Generated cache key: {cache_key}")
    
    # Check if result is already cached
    cached_result = get_cache(cache_key)
    if cached_result:
        logger.info(f"Returning cached result for model {model_id}")
        return cached_result
    
    try:
        input_obj = model.Input(**input_data)
        result = model.predict(input_obj)
        logger.info(f"Model {model_id} executed successfully with result: {result}")
        
        # Cache the result with an expiration time
        set_cache(cache_key, result.dict())
        logger.info(f"Cached result for model {model_id} with key {cache_key}")
        
        return result.dict()
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
    
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    if loop.is_running():
        # If there's an existing event loop, create a task
        loop.create_task(update_task())
    else:
        # Otherwise, run the coroutine
        loop.run_until_complete(update_task())