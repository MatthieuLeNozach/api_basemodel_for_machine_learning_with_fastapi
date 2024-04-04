# file: app/dev_tools.py
"""
Module: dev_tools.py

This module provides development utility functions for managing superuser accounts
in the application. It includes functions to create and remove a superuser account
with predefined credentials and permissions.

The module uses SQLAlchemy to interact with the database and the `passlib` library
for password hashing.

Functions:
- `create_superuser(db: Session)`: Creates a superuser account with the following details:
    - Username: 'superuser@example.com'
    - First Name: 'Super'
    - Last Name: 'User'
    - Password: '8888' (hashed using bcrypt)
    - Active: True
    - Role: 'admin'
    - Access V1: True
    - Access V2: True

- `remove_superuser(db: Session)`: Removes the superuser account with the username
  'superuser@example.com' from the database.

Note: These functions are intended for development and testing purposes only and
should not be used in a production environment. Make sure to properly secure and
manage superuser accounts in a production setup.

Dependencies:
- `sqlalchemy.orm.Session`: The SQLAlchemy Session class for database operations.
- `models.User`: The User model class representing the user table in the database.
- `passlib.context.CryptContext`: The password hashing context from the `passlib` library.
"""

from sqlalchemy.orm import Session
from passlib.context import CryptContext
from .models import User

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def create_superuser(db: Session) -> None:
    """
    Creates a superuser in the database.

    Args:
        db (Session): The database session.

    Returns:
        None

    Notes:
        - This function creates a superuser with predefined credentials and permissions.
        - The superuser has the username 'superuser@example.com' and password '8888'.
        - The superuser is assigned the 'admin' role and has access to both v1 and v2.

    Example usage:
        db = SessionLocal()
        create_superuser(db)
    """
    superuser = User(
        username="superuser@example.com",
        first_name="Super",
        last_name="User",
        hashed_password=pwd_context.hash("8888"),
        is_active=True,
        role="admin",
        has_access_v1=True,
        has_access_v2=True,
    )
    db.add(superuser)
    db.commit()


def remove_superuser(db: Session) -> None:
    """
    Removes the superuser from the database.

    Args:
        db (Session): The database session.

    Returns:
        None

    Notes:
        - This function removes the superuser with the username 'superuser@example.com' from the database.
        - It deletes the superuser record and commits the changes to the database.

    Example usage:
        db = SessionLocal()
        remove_superuser(db)
    """
    db.query(User).filter(User.username == "superuser@example.com").delete()
    db.commit()
