import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi.testclient import TestClient
from project.fu_core.users.models import User
from sqlalchemy import text
def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "hello world"}







@pytest.mark.asyncio
async def test_create_user(db_session, user_factory):
    async with db_session() as session:
        user = user_factory.build()  # Build the user without saving
        session.add(user)
        await session.commit()

        # Verify the user was actually saved
        result = await session.execute(select(User).where(User.id == user.id))
        saved_user = result.scalar_one_or_none()

        assert saved_user is not None
        assert saved_user.email == user.email
        assert saved_user.is_active == user.is_active
        assert saved_user.is_superuser == user.is_superuser
        assert saved_user.is_verified == user.is_verified