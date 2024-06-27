from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from uuid import UUID

from project.inference.models import (
    InferenceModel, 
    ServiceCall, 
    UserAccess,
    AccessPolicy
) 


async def create_access_policy(
    session: AsyncSession,
    name: str,
    daily_api_calls: int = 1000,
    monthly_api_calls: int = 30000
) -> AccessPolicy:
    new_policy = AccessPolicy(
        name=name,
        daily_api_calls=daily_api_calls,
        monthly_api_calls=monthly_api_calls
    )
    session.add(new_policy)
    await session.commit()
    await session.refresh(new_policy)
    return new_policy

async def create_inference_model(
    session: AsyncSession,
    name: str,
    access_policy_id: int,
    problem: str,
    category: str | None = None,
    version: str | None = None,
) -> InferenceModel:
    new_model = InferenceModel(
        name=name,
        access_policy_id=access_policy_id,
        problem=problem,
        category=category, 
        version=version
    )
    session.add(new_model)
    await session.commit()
    await session.refresh(new_model)
    return new_model



async def get_access_policy(session: AsyncSession, policy_id: int) -> AccessPolicy:
    result = await session.execute(select(AccessPolicy).where(AccessPolicy.id == policy_id))
    return result.scalars().first()

def add_placeholder_model():
    create_inference_model(
        name= "linreg_placeholder",
        problem="regression",
        category="linear",
        version="0.0.1"
        
    )
    
    
async def create_user_access(
    session: AsyncSession,
    user_id: UUID,
    model_id: int,
    access_policy_id: int
) -> UserAccess:
    new_user_access = UserAccess(
        user_id=user_id,
        model_id=model_id,
        access_policy_id=access_policy_id
    )
    session.add(new_user_access)
    await session.commit()
    await session.refresh(new_user_access)
    return new_user_access


    
async def get_inference_model(session: AsyncSession, model_id: int) -> InferenceModel:
    result = await session.execute(select(InferenceModel).where(InferenceModel.id == model_id))
    return result.scalars().first()


async def create_service_call(
    session: AsyncSession, model_id: int, user_id: UUID, celery_task_id: str | None = None
) -> ServiceCall:
    new_service_call = ServiceCall(
        model_id=model_id, user_id=user_id, celery_task_id=celery_task_id
    )
    session.add(new_service_call)
    await session.commit()
    await session.refresh(new_service_call)
    return new_service_call


async def get_service_call(session: AsyncSession, service_call_id: int) -> ServiceCall:
    result = await session.execute(select(ServiceCall).where(ServiceCall.id == service_call_id))
    return result.scalars().first()