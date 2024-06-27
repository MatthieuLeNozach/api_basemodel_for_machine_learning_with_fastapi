from celery.result import AsyncResult
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from project.database import get_async_session
from project.fu_core.users import current_superuser, current_active_user, models
from project.inference import crud, inference_router, schemas, tasks
from project.inference.model_registry import model_registry


@inference_router.get("/predict-os/")
async def predict_os():
    task = tasks.run_regression.delay()  # Trigger the Celery task
    return JSONResponse({"task_id": task.task_id})


@inference_router.get("/predict/{model_id}")
async def predict(
    model_id: int,
    current_user: models.User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):
    user_id: UUID = current_user.id
    
    if model_id not in model_registry:
        raise HTTPException(status_code=404, detail=f"Model with id {model_id} not found")
    
     # Check if the user has access to the model and update their access record
    has_access, message = await crud.check_user_access_and_update(
        session, user_id, model_id
    )
    if not has_access:
        raise HTTPException(status_code=403, detail=message)
    
    # Create a service call record
    service_call = await crud.create_service_call(session, model_id, user_id)
    
    task = tasks.run_model.delay(model_id)
    service_call.celery_task_id = task.task_id
    await session.commit()
    
    
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
    user_access: schemas.UserAccessCreate,
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