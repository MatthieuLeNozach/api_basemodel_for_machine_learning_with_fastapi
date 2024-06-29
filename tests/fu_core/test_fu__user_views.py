import pytest
from fastapi import status
from typing import Dict, Any, cast
from tests.factories import UserFactory
from sqlalchemy.ext.asyncio import AsyncSession
from project.fu_core.users import UserManager
from project.fu_core.security import auth_backend

@pytest.mark.asyncio
async def test_missing_token(client):
    response = client.get("/api/v1/users/me")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
@pytest.mark.asyncio
async def test_inactive_user(client, db_session):
    async with db_session() as session:
        # Set the session for the UserFactory
        UserFactory._meta.sqlalchemy_session = session

        # Create an inactive user
        user = UserFactory(is_active=False)
        session.add(user)
        await session.commit()

        # Reset the session for the UserFactory
        UserFactory._meta.sqlalchemy_session = None

    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {user.token}"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    
    
    
@pytest.mark.asyncio
async def test_inactive_user(client, db_session: AsyncSession):
    async with db_session() as session:
        # Set the session for the UserFactory
        UserFactory._meta.sqlalchemy_session = session

        # Create an inactive user
        user = UserFactory(is_active=False)
        session.add(user)
        await session.commit()

        # Generate a token for the user
        user_manager = UserManager(session)
        token = await auth_backend.get_strategy().write_token(user)

        # Reset the session for the UserFactory
        UserFactory._meta.sqlalchemy_session = None

    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    

@pytest.mark.asyncio
async def test_active_user(client, db_session):
    async with db_session() as session:
        # Set the session for the UserFactory
        UserFactory._meta.sqlalchemy_session = session

        # Create an active user
        user = UserFactory(is_active=True)
        session.add(user)
        await session.commit()

        # Generate a token for the user
        user_manager = UserManager(session)
        token = await auth_backend.get_strategy().write_token(user)

        # Reset the session for the UserFactory
        UserFactory._meta.sqlalchemy_session = None

    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == user.email
    
    
    
    
@pytest.mark.asyncio
async def test_verified_user(client, db_session: AsyncSession):
    async with db_session() as session:
        # Set the session for the UserFactory
        UserFactory._meta.sqlalchemy_session = session

        # Create a verified user
        user = UserFactory(is_verified=True)
        session.add(user)
        await session.commit()

        # Generate a token for the user
        user_manager = UserManager(session)
        token = await auth_backend.get_strategy().write_token(user)

        # Reset the session for the UserFactory
        UserFactory._meta.sqlalchemy_session = None

    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == user.email
    
@pytest.mark.asyncio
async def test_superuser(client, db_session: AsyncSession):
    async with db_session() as session:
        # Set the session for the UserFactory
        UserFactory._meta.sqlalchemy_session = session

        # Create a superuser
        user = UserFactory(is_active=True, is_superuser=True)
        session.add(user)
        await session.commit()

        # Generate a token for the superuser
        user_manager = UserManager(session)
        token = await auth_backend.get_strategy().write_token(user)

        # Reset the session for the UserFactory
        UserFactory._meta.sqlalchemy_session = None

    response = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == user.email
    assert data["is_superuser"] is True
    
