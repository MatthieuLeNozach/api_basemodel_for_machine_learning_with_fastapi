from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
from celery.result import AsyncResult
from project.inference.tasks import run_regression
from project.inference import inference_router

 
@inference_router.get("/predict/")
async def predict():
    task = run_regression.delay()  # Trigger the Celery task
    return JSONResponse({"task_id": task.task_id})

@inference_router.get("/task_status/{task_id}")
def task_status(task_id: str):
    task = AsyncResult(task_id)
    state = task.state
    if state == 'FAILURE':
        error = str(task.result)
        response = {'state': state, 'error': error}
    else:
        response = {'state': state, 'result': task.result}
    return JSONResponse(response)