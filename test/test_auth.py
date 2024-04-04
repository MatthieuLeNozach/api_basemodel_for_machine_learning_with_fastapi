# file: test/test_auth.py

from .utils import *

from jose import jwt
from datetime import timedelta
from fastapi import HTTPException
import pytest

from ..app.schemas import TokenData
from ..app.routers.auth import (
    get_db,
    authenticate_user,
    create_access_token,
    SECRET_KEY,
    ALGORITHM,
    get_current_user,
)

app.dependency_overrides[get_db] = override_get_db


def test_authenticate_user(test_superuser):
    with TestingSessionLocal() as db:

        authenticated_user = authenticate_user(test_superuser.username, "8888", db)
        assert authenticated_user is not None
        assert authenticated_user.username == test_superuser.username

        non_existent_user = authenticate_user("WrongUserName", "testpassword", db)
        assert non_existent_user is False

        wrong_password_user = authenticate_user(
            test_superuser.username, "wrongpassword", db
        )
        assert wrong_password_user is False


def test_create_access_token():
    token_data = TokenData(
        username="testy_mc_testface@example.com",
        user_id=1,
        role="admin",
        has_access_v1=True,
        has_access_v2=True,
        expires_delta=timedelta(days=1),
    )

    token = create_access_token(token_data)

    decoded_token = jwt.decode(
        token, SECRET_KEY, algorithms=[ALGORITHM], options={"verify_signature": False}
    )

    assert decoded_token["username"] == token_data.username
    assert decoded_token["user_id"] == token_data.user_id
    assert decoded_token["role"] == token_data.role


@pytest.mark.asyncio
async def test_get_current_user_valid_token():
    encode = {
        "username": "testy_mc_testface@example.com",
        "user_id": 1,
        "role": "admin",
        "has_access_v1": True,
        "has_access_v2": True,
    }
    token = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

    user = await get_current_user(token=token)
    assert user["username"] == "testy_mc_testface@example.com"
    assert user["id"] == 1
    assert user["role"] == "admin"
    assert user["has_access_v1"] is True
    assert user["has_access_v2"] is True


@pytest.mark.asyncio
async def test_get_current_user_missing_payload():
    encode = {"role": "user"}
    token = jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

    with pytest.raises(HTTPException) as excinfo:
        await get_current_user(token=token)

    assert excinfo.value.status_code == 401
    assert excinfo.value.detail == "Could not validate user"


def test_create_user():
    user_data = {
        "username": "usy_mc_userface@example.com",
        "first_name": "Usy",
        "last_name": "McUserface",
        "password": "8888",
    }

    response = client.post("/auth/create", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED

    with TestingSessionLocal() as db:
        user = db.query(User).filter_by(username=user_data["username"]).first()
        assert user is not None
        assert user.username == user_data["username"]
        assert user.first_name == user_data["first_name"]
        assert user.last_name == user_data["last_name"]
        assert bcrypt_context.verify(user_data["password"], user.hashed_password)
        assert user.is_active == True
        assert user.has_access_v1 == False
        assert user.has_access_v2 == False
        assert user.role == "user"
