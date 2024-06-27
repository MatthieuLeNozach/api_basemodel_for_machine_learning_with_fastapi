import asyncio
from celery.result import AsyncResult
from celery import shared_task
from celery.signals import task_failure, task_success
from project.inference.model_registry import model_registry
from project.database import get_async_session
from project.inference.crud import update_service_call_time_completed


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



@shared_task
def run_model(model_id: int):
    if model_id not in model_registry:
        return {"error": f"Model with id {model_id} not found"}
    
    model_func = model_registry[model_id]
    return model_func()


@task_success.connect(sender=run_model)
def task_success_handler(sender, result, **kwargs):
    task_id = sender.request.id
    task_result = AsyncResult(task_id)
    time_completed = task_result.date_done

    async def update_task():
        async for session in get_async_session():
            await update_service_call_time_completed(session, task_id, time_completed)
    
    asyncio.run(update_task())