from fastapi import Depends
from fastapi_users.db import (
    SQLAlchemyAccessTokenDatabase,
    SQLAlchemyBaseAccessTokenTableUUID,
)
from sqlalchemy.ext.asyncio import AsyncSession

from project.database import Base, get_async_session


class AccessToken(SQLAlchemyBaseAccessTokenTableUUID, Base):
    pass


async def get_access_token_db(
    session: AsyncSession = Depends(get_async_session),
):
    yield SQLAlchemyAccessTokenDatabase(session, AccessToken)
