# file: test/test_admin.py

from fastapi import status

from .utils import *
from ..app.routers.admin import get_db, get_current_user
from ..app.models import User



app.dependency_overrides[get_db] = override_get_db
app.dependency_overrides[get_current_user] = override_get_current_user

def test_admin_get_all_users(test_superuser, test_regular_users_revoked):
    response = client.get("/admin/users")
    assert response.status_code == status.HTTP_200_OK

    users = response.json()
    assert isinstance(users, list)
    assert any(user["username"] == "testy_mc_testface@example.com" for user in users)
    assert len(users) == 5
    for i in range(4):
        assert any(user["username"] == f"user{i}@example.com" for user in users)


def test_create_admin(test_superuser):
    user_data = {
        "username": "admy_mc_adminface@example.com",
        "first_name": "Admy",
        "last_name": "McAdminface",
        "password": "8888",
    }

    response = client.post("/admin/create", json=user_data)
    assert response.status_code == status.HTTP_201_CREATED

    with TestingSessionLocal() as db:
        user = db.query(User).filter_by(username=user_data["username"]).first()
        assert user is not None
        assert user.username == user_data["username"]
        assert user.first_name == user_data["first_name"]
        assert user.last_name == user_data["last_name"]
        assert bcrypt_context.verify(user_data["password"], user.hashed_password)
        assert user.is_active == True
        assert user.has_access_v1 == True
        assert user.has_access_v2 == True
        assert user.role == "admin"


def test_admin_grant_user_access_rights(test_superuser, test_regular_users_revoked):
    with TestingSessionLocal() as db:
        for user in test_regular_users_revoked:
            new_access_rights = {
                "is_active": True,
                "has_access_v1": True,
                "has_access_v2": True,
            }
            response = client.put(f"/admin/users/{user.id}", json=new_access_rights)
            assert response.status_code == status.HTTP_204_NO_CONTENT

            modified_user = db.query(User).filter(User.id == user.id).first()
            assert modified_user.is_active == True
            assert modified_user.has_access_v1 == True
            assert modified_user.has_access_v2 == True


def test_admin_revoke_user_access_rights(test_superuser, test_regular_users_granted):
    with TestingSessionLocal() as db:
        for user in test_regular_users_granted:
            new_access_rights = {
                "is_active": False,
                "has_access_v1": False,
                "has_access_v2": False,
            }
            response = client.put(f"/admin/users/{user.id}", json=new_access_rights)
            print("Response.content: ", response.content)
            assert response.status_code == status.HTTP_204_NO_CONTENT

            db_user = db.query(User).filter(User.id == user.id).first()

            assert db_user.is_active == False
            assert db_user.has_access_v1 == False
            assert db_user.has_access_v2 == False


def test_admin_delete_user(test_superuser, test_regular_users_granted):
    with TestingSessionLocal() as db:
        response = client.delete(f"/admin/users/2")
        assert response.status_code == status.HTTP_204_NO_CONTENT
