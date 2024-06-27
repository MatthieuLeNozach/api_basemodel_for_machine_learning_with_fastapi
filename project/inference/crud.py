from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from datetime import datetime, timedelta, timezone
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


async def get_access_policy_by_name(session: AsyncSession, name: str) -> AccessPolicy | None:
    result = await session.execute(select(AccessPolicy).where(AccessPolicy.name == name))
    return result.scalars().first()


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



async def get_access_policy(
    session: AsyncSession, policy_id: int
) -> AccessPolicy | None:
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


    
async def get_inference_model(session: AsyncSession, model_id: int) -> InferenceModel | None:
    result = await session.execute(select(InferenceModel).where(InferenceModel.id == model_id))
    return result.scalars().first()


async def create_service_call(
    session: AsyncSession, 
    model_id: int, 
    user_id: UUID, 
    celery_task_id: str | None = None
) -> ServiceCall:
    new_service_call = ServiceCall(
        model_id=model_id, user_id=user_id, celery_task_id=celery_task_id
    )
    session.add(new_service_call)
    await session.commit()
    await session.refresh(new_service_call)
    return new_service_call


async def get_service_call(session: AsyncSession, service_call_id: int) -> ServiceCall | None:
    result = await session.execute(select(ServiceCall).where(ServiceCall.id == service_call_id))
    return result.scalars().first()


async def update_service_call_time_completed(
    session: AsyncSession, task_id: str, time_completed: datetime
):
    async with session.begin():
        result = await session.execute(
            select(ServiceCall).where(ServiceCall.celery_task_id == task_id)
        )
        service_call = result.scalars().first()
        if service_call:
            service_call.time_completed = time_completed
            session.add(service_call)
            await session.commit()


async def get_user_access(
    session: AsyncSession, user_id: UUID, model_id: int
) -> UserAccess | None:
    result = await session.execute(
        select(UserAccess).where(
            UserAccess.user_id == user_id,
            UserAccess.model_id == model_id,
            UserAccess.access_granted == True
        )
    )
    return result.scalars().first()


async def check_daily_limit(
    session: AsyncSession, user_id: UUID, model_id: int, access_policy: AccessPolicy
) -> bool:
    today = datetime.now(timezone.utc).date()
    result = await session.execute(
        select(func.count(ServiceCall.id)).where(
            ServiceCall.user_id == user_id,
            ServiceCall.model_id == model_id,
            func.date(ServiceCall.time_requested) == today
        )
    )
    daily_calls = result.scalar_one_or_none()
    return (daily_calls or 0) < access_policy.daily_api_calls



async def check_monthly_limit(
    session: AsyncSession, user_id: UUID, model_id: int, access_policy: AccessPolicy
) -> bool:
    first_day_of_month = datetime.now(timezone.utc).replace(day=1)
    result = await session.execute(
        select(func.count(ServiceCall.id)).where(
            ServiceCall.user_id == user_id,
            ServiceCall.model_id == model_id,
            ServiceCall.time_requested >= first_day_of_month
        )
    )
    monthly_calls = result.scalar_one_or_none()
    return (monthly_calls or 0) < access_policy.monthly_api_calls


async def update_user_access(session: AsyncSession, user_access: UserAccess):
    user_access.api_calls += 1
    user_access.last_accessed = func.now() # datetime.utcnow()
    await session.commit()
    
    
    
async def check_user_access_and_update(
    session: AsyncSession, user_id: UUID, model_id: int
) -> tuple[bool, str]:
    user_access = await get_user_access(session, user_id, model_id)
    
    if not user_access:
        return False, "User does not have access to this model"
    
    access_policy = await get_access_policy(session, user_access.access_policy_id)
    
    if not access_policy:
        return False, "Access policy not found"
    
    if not await check_daily_limit(session, user_id, model_id, access_policy):
        return False, "Daily API call limit exceeded"
    
    if not await check_monthly_limit(session, user_id, model_id, access_policy):
        return False, "Monthly API call limit exceeded"
    
    await update_user_access(session, user_access)
    
    return True, "Access granted"



