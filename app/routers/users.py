# file: users.py
"""
Module: users.py

This module provides API endpoints for user-related operations. It uses the FastAPI framework
to define routes and handle HTTP requests. The module includes the following main components:

- Dependencies:
  - `get_db`: Dependency function to get a database session.
  - `get_current_user`: Dependency function to authenticate and retrieve the current user.
  - `bcrypt_context`: CryptContext instance for password hashing.

- Routes:
  - `/`: Endpoint to retrieve the current user's information.
  - `/password`: Endpoint to change the user's password.

The module integrates with the `User` model and `UserVerification` and `ReadUser` schemas for data
validation and storage. It also uses the `get_current_user` dependency for authentication.

Password hashing is performed using the `bcrypt` algorithm through the `CryptContext` class from
the `passlib` library.
"""

from typing import Annotated

from fastapi import APIRouter, status, HTTPException, Depends
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from ..models import User
from ..schemas import UserVerification, ReadUser
from ..database import get_db
from .auth import get_current_user


router = APIRouter(prefix="/user", tags=["user"])

############### DEPENDENCIES ###############
db_dependency = Annotated[Session, Depends(get_db)]  # pylint: disable=invalid-name
user_dependency = Annotated[
    dict, Depends(get_current_user)
]  # pylint: disable=invalid-name
bcrypt_context = CryptContext(
    schemes=["bcrypt"], deprecated="auto"
)  # pylint: disable=invalid-name


############### ROUTES ###############
@router.get("/", status_code=status.HTTP_200_OK, response_model=ReadUser)
async def get_user(user: user_dependency, db: db_dependency) -> User:
    """
    Endpoint to retrieve the current user's information.

    Args:
        user: The authenticated user dependency.
        db: The database session dependency.

    Returns:
        User: The current user's information.

    Raises:
        HTTPException: If the user is not authenticated.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )
    return db.query(User).filter(User.id == user.get("id")).first()


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    user: user_dependency, db: db_dependency, user_verification: UserVerification
) -> None:
    """
    Endpoint to change the user's password.

    Args:
        user: The authenticated user dependency.
        db: The database session dependency.
        user_verification: The UserVerification schema containing the current and new passwords.

    Returns:
        None

    Raises:
        HTTPException: If the user is not authenticated or if the current password is incorrect.
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication failed"
        )

    user_model = db.query(User).filter(User.id == user.get("id")).first()
    if not bcrypt_context.verify(
        user_verification.password, user_model.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Error on password change"
        )
    user_model.hashed_password = bcrypt_context.hash(user_verification.new_password)
    db.add(user_model)
    db.commit()
