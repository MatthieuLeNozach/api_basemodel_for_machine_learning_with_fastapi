import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.testclient import TestClient

def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "hello world"}

@pytest.mark.asyncio()
async def test_create_user(db_session: AsyncSession, user_factory):
    user = user_factory()
    db_session.add(user)
    await db_session.commit()
    assert user.email is not None