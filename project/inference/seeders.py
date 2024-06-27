from sqlalchemy.ext.asyncio import AsyncSession
from project.inference.crud import (
    create_inference_model, 
    create_access_policy, 
    get_access_policy_by_name,
    get_inference_model
)

from project.inference.model_registry import model_registry


async def add_base_access_policy(session: AsyncSession):
    existing_policy = await get_access_policy_by_name(session, "base")
    if not existing_policy:
        await create_access_policy(
            session,
            name="base",
        )

async def add_models_from_registry(session: AsyncSession):
    for model_id, model_info in model_registry.items():
        existing_model = await get_inference_model(session, model_id)
        if not existing_model:
            await create_inference_model(
                session,
                name=model_info["name"],
                problem=model_info["problem"],
                category=model_info["category"],
                version=model_info["version"],
                access_policy_id=model_info["access_policy_id"]
            )



async def seed_inference_data(session: AsyncSession):
    await add_base_access_policy(session)
    await add_models_from_registry(session)
    # Add other seeders here