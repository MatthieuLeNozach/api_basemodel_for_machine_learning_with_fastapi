import pytest
from fastapi import status
from typing import Dict, Any, cast
from tests.factories import UserFactory
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from project.fu_core.users.models import User

@pytest.mark.asyncio
async def test_empty_body(client):
    response = client.post("/api/v1/auth/register", json={})
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_missing_email(client):
    json = {"password": "guinevere"}
    response = client.post("/api/v1/auth/register", json=json)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_missing_password(client):
    json = {"email": "king.arthur@camelot.bt"}
    response = client.post("/api/v1/auth/register", json=json)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

@pytest.mark.asyncio
async def test_wrong_email(client):
    json = {"email": "king.arthur", "password": "guinevere"}
    response = client.post("/api/v1/auth/register", json=json)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

# @pytest.mark.asyncio
# async def test_invalid_password(client):
#     json = {"email": "king.arthur@camelot.bt", "password": "g"}
#     response = client.post("/api/v1/auth/register", json=json)
#     assert response.status_code == status.HTTP_400_BAD_REQUEST
#     data = cast(Dict[str, Any], response.json())
#     assert data["detail"] == {
#         "code": "REGISTER_INVALID_PASSWORD",
#         "reason": "Password should be at least 3 characters",
#     }

@pytest.mark.asyncio
@pytest.mark.parametrize("email", ["king.arthur@camelot.bt", "King.Arthur@camelot.bt"])
async def test_existing_user(email, client, db_session):
    async with db_session() as session:
        # Set the session for the UserFactory
        UserFactory._meta.sqlalchemy_session = session

        # Create an existing user
        user = UserFactory(email=email, hashed_password="guinevere")
        session.add(user)
        await session.commit()

        # Reset the session for the UserFactory
        UserFactory._meta.sqlalchemy_session = None

    json = {"email": email, "password": "guinevere"}
    response = client.post("/api/v1/auth/register", json=json)
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = cast(Dict[str, Any], response.json())
    assert data["detail"] == "REGISTER_USER_ALREADY_EXISTS"
    
    

@pytest.mark.asyncio
@pytest.mark.parametrize("email", ["lancelot@camelot.bt", "Lancelot@camelot.bt"])
async def test_valid_body(email, client, db_session: AsyncSession):
    json = {"email": email, "password": "guinevere"}
    response = client.post("/api/v1/auth/register", json=json)
    assert response.status_code == status.HTTP_201_CREATED

    data = cast(Dict[str, Any], response.json())
    assert "hashed_password" not in data
    assert "password" not in data
    assert data["id"] is not None

@pytest.mark.asyncio
async def test_valid_body_is_superuser(client, db_session: AsyncSession):
    json = {
        "email": "lancelot@camelot.bt",
        "password": "guinevere",
        "is_superuser": True,
    }
    response = client.post("/api/v1/auth/register", json=json)
    assert response.status_code == status.HTTP_201_CREATED

    data = cast(Dict[str, Any], response.json())
    assert data["is_superuser"] is False

@pytest.mark.asyncio
async def test_valid_body_is_active(client, db_session: AsyncSession):
    json = {
        "email": "lancelot@camelot.bt",
        "password": "guinevere",
        "is_active": False,
    }
    response = client.post("/api/v1/auth/register", json=json)
    assert response.status_code == status.HTTP_201_CREATED

    data = cast(Dict[str, Any], response.json())
    assert data["is_active"] is True
    
    
@pytest.mark.asyncio
async def test_existing_email(client, db_session: AsyncSession):
    async with db_session() as session:
        # Set the session for the UserFactory
        UserFactory._meta.sqlalchemy_session = session

        # Create and commit a user with the existing email
        user = UserFactory(email="existing@example.com")
        session.add(user)
        await session.commit()

        # Verify the user is in the database
        result = await session.execute(select(User).where(User.email == "existing@example.com"))
        existing_user = result.scalar_one_or_none()
        assert existing_user is not None, "User with email 'existing@example.com' was not found in the database"

        # Reset the session for the UserFactory
        UserFactory._meta.sqlalchemy_session = None

    # Attempt to register a new user with the same email
    json = {"email": "existing@example.com", "password": "password123"}
    response = client.post("/api/v1/auth/register", json=json)
    
    # Log the response for debugging
    print(f"Response status code: {response.status_code}")
    print(f"Response content: {response.json()}")

    # Assert the response status and detail
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    data = response.json()
    assert data["detail"] == "REGISTER_USER_ALREADY_EXISTS"