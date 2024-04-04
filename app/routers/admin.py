# file: app/routers/admin.py
"""
Module: admin.py

This module provides API endpoints for admin-related operations. It uses the FastAPI framework
to define routes and handle HTTP requests. The module includes the following main components:

- Dependencies:
  - `get_db`: Dependency function to get a database session.
  - `get_current_user`: Dependency function to authenticate and retrieve the current user.
  - `bcrypt_context`: CryptContext instance for password hashing.

- Routes:
  - `/users`: Endpoint to retrieve all users (admin only).
  - `/create`: Endpoint to create a new admin user.
  - `/users/{user_id}` (PUT): Endpoint to change user access rights (admin only).
  - `/users/{user_id}` (DELETE): Endpoint to delete a user (admin only).

The module integrates with the `User` model and `ChangeUserAccessRights`, `ReadUser`, and `CreateAdmin`
schemas for data validation and storage. It also uses the `get_current_user` dependency for authentication.

Password hashing is performed using the `bcrypt` algorithm through the `CryptContext` class from
the `passlib` library.
"""
from typing import Annotated, List
from fastapi import Depends, status, HTTPException, Path, APIRouter, Body
from pydantic import ValidationError
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import ChangeUserAccessRights, ReadUser, CreateAdmin
from .auth import get_current_user, bcrypt_context

router = APIRouter(prefix="/admin", tags=["admin"])


db_dependency = Annotated[Session, Depends(get_db)]  # pylint: disable=invalid-name
user_dependency = Annotated[
    dict, Depends(get_current_user)
]  # pylint: disable=invalid-name


############### ROUTES ###############
@router.get("/users", status_code=status.HTTP_200_OK, response_model=List[ReadUser])
async def get_all_users(user: user_dependency, db: db_dependency) -> list:
    """
    Retrieves all users (admin only).

    Args:
        user: The authenticated user (admin only).
        db: The database session.

    Returns:
        A list of all users.

    Raises:
        HTTPException: If the user is not authenticated or not an admin.
    """
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return db.query(User).all()


@router.post("/create", status_code=status.HTTP_201_CREATED)
async def create_admin(db: db_dependency, create_user_request: CreateAdmin) -> None:
    """
    Creates a new admin user.

    Args:
        db: The database session.
        create_user_request: The request data for creating an admin user.

    Returns:
        None

    Raises:
        ValidationError: If the request data is invalid.
    """
    try:
        CreateAdmin.parse_obj(create_user_request.dict())
        password = create_user_request.password
        create_admin_model = User(**create_user_request.dict(exclude={"password"}))
        create_admin_model.hashed_password = bcrypt_context.hash(password)

        db.add(create_admin_model)
        db.commit()

    except ValidationError as e:
        print(f"Validation Error: {e}")
        return {"detail": str(e)}


@router.put("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def change_user_access_rights(
    user: user_dependency,
    db: db_dependency,
    user_id: int = Path(gt=0),
    access_rights: ChangeUserAccessRights = Body(...),
) -> None:
    """
    Changes the access rights of a user (admin only).

    Args:
        user: The authenticated user (admin only).
        db: The database session.
        user_id: The ID of the user to modify.
        access_rights: The new access rights for the user.

    Returns:
        None

    Raises:
        HTTPException: If the user is not authenticated, not an admin, or the user to modify is not found.
    """
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)

    modified_user = db.query(User).filter(User.id == user_id).first()
    if modified_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    modified_user.is_active = access_rights.is_active
    modified_user.has_access_v1 = access_rights.has_access_v1
    modified_user.has_access_v2 = access_rights.has_access_v2
    db.add(modified_user)
    db.commit()
    db.refresh(modified_user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user: user_dependency, db: db_dependency, user_id: int = Path(gt=0)
) -> None:
    """
    Deletes a user (admin only).

    Args:
        user: The authenticated user (admin only).
        db: The database session.
        user_id: The ID of the user to delete.

    Returns:
        None

    Raises:
        HTTPException: If the user is not authenticated or not an admin.
    """
    if user is None or user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )

    # pylint: disable=E1101
    user_model = (
        db.query(User).filter(User.id == user_id).delete()
    )  # pylint: disable=unused-variable
    db.commit()
