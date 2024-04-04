# file: test/test_users.py

from fastapi import status

from .utils import *
from ..app.routers.users import get_db, get_current_user


app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user


def test_return_user(test_superuser):
    response = client.get("/user")
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["username"] == "testy_mc_testface@example.com"
    assert response.json()["first_name"] == "Testy"
    assert response.json()["last_name"] == "McTestface"
    assert response.json()["role"] == "admin"


def test_change_password_success(test_superuser):
    response = client.put(
        "/user/password", json={"password": "8888", "new_password": "666666"}
    )
    if response.status_code != status.HTTP_204_NO_CONTENT:
        print(response.json())  # This will print the validation error details
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_change_password_invalid_current_password(test_superuser):
    response = client.put(
        "/user/password", json={"password": "888", "new_password": "666666"}
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {"detail": "Error on password change"}
