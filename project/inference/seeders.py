from sqlalchemy.ext.asyncio import AsyncSession
from project.inference.crud import create_inference_model, create_access_policy



async def add_base_access_policy(session: AsyncSession):
    await create_access_policy(
        session,
        name="base",
    )

async def add_placeholder_model(session: AsyncSession):
    await create_inference_model(
        session,
        name="linreg_placeholder",
        problem="regression",
        category="linear",
        version="0.0.1",
        access_policy_id=0
    )


async def seed_inference_data(session: AsyncSession):
    await add_base_access_policy(session)
    await add_placeholder_model(session)
    # Add other seeders here