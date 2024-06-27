from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from project.database import get_async_session

async def get_session() -> AsyncSession:
    async with get_async_session() as session:
        yield session