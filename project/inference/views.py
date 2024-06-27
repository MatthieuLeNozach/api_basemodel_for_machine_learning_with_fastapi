from fastapi import FastAPI, UploadFile, File, Depends
from fastapi.responses import JSONResponse
from celery.result import AsyncResult
from project.inference.tasks import run_regression
from project.inference import inference_router
from project.fu_core.users import models, current_superuser
from project.inference import schemas, crud
from sqlalchemy.ext.asyncio import AsyncSession
from project.database import get_async_session

 
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



@inference_router.post('/pair_user_model', response_model=schemas.UserAccessResponse)
async def pair_user_model(
    user_access = schemas.UserAccessCreate,
    session: AsyncSession = Depends(get_async_session),
    superuser: models.User = Depends(current_superuser)
):
    user_access_db = await crud.create_user_access(
        session,
        user_access.user_id,
        user_access.model_id,
        user_access.access_policy_id
    )
    return  user_access_db