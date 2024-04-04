# file: app/models.py
"""
Module: models.py

This module defines the database models for the application using SQLAlchemy ORM.
It includes the following models:

1. User:
   - Represents a user in the system.
   - Attributes:
     - id: The primary key of the user.
     - username: The unique username of the user.
     - first_name: The first name of the user.
     - last_name: The last name of the user.
     - country: The country of the user (optional).
     - hashed_password: The hashed password of the user.
     - is_active: Indicates whether the user is active.
     - role: The role of the user.
     - has_access_v1: Indicates whether the user has access to version 1.
     - has_access_v2: Indicates whether the user has access to version 2.
   - Relationships:
     - service_calls: The service calls associated with the user.

2. ServiceCall:
   - Represents a service call made by a user.
   - Attributes:
     - id: The primary key of the service call.
     - service_version: The version of the service called.
     - success: Indicates whether the service call was successful.
     - owner_id: The foreign key referencing the user who made the service call.
     - request_time: The timestamp of when the service call was requested.
     - completion_time: The timestamp of when the service call was completed.
     - duration: The duration of the service call.
   - Relationships:
     - user: The user who made the service call.

The models are defined using SQLAlchemy's declarative base class `Base` from the
`database` module. They use the `Mapped` and `mapped_column` constructs from
SQLAlchemy 2.0 for defining the model attributes and relationships.

The `User` model has a one-to-many relationship with the `ServiceCall` model,
where each user can have multiple service calls associated with them.

Note: Make sure to run the necessary database migrations or create the corresponding
tables in the database based on these model definitions.
"""

from sqlalchemy import Float, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base


class User(Base):
    """
    Represents a user in the system.

    Attributes:
        id (int): The unique identifier of the user.
        username (str): The username of the user.
        first_name (str): The first name of the user.
        last_name (str): The last name of the user.
        country (str): The country of the user (optional).
        hashed_password (str): The hashed password of the user.
        is_active (bool): Indicates whether the user is active.
        role (str): The role of the user.
        has_access_v1 (bool): Indicates whether the user has access to version 1.
        has_access_v2 (bool): Indicates whether the user has access to version 2.
        service_calls (list): The service calls associated with the user.

    Methods:
        __init__(self, **kwargs): Initializes a new instance of the User class.

    """

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(127), unique=True)
    first_name: Mapped[str] = mapped_column(String(127))
    last_name: Mapped[str] = mapped_column(String(127))
    country: Mapped[str] = mapped_column(String(127), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String(255))
    has_access_v1: Mapped[bool] = mapped_column(Boolean, default=False)
    has_access_v2: Mapped[bool] = mapped_column(Boolean, default=False)
    service_calls = relationship("ServiceCall", back_populates="user")


class ServiceCall(Base):
    """
    Represents a service call made by a user.

    Attributes:
        id (str): The unique identifier of the service call.
        service_version (str): The version of the service called.
        success (bool): Indicates whether the service call was successful.
        owner_id (int): The ID of the user who made the service call.
        request_time (DateTime): The timestamp of when the service call was requested.
        completion_time (DateTime): The timestamp of when the service call was completed.
        duration (float): The duration of the service call in seconds.
        user (User): The user associated with the service call.

    Methods:
        __init__(self, **kwargs): Initializes a new instance of the ServiceCall class.

    """

    __tablename__ = "service_calls"

    id: Mapped[str] = mapped_column(Integer, primary_key=True, index=True)
    service_version: Mapped[str] = mapped_column(String(2))
    # priority: Mapped[int] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"))
    request_time: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    completion_time: Mapped[DateTime] = mapped_column(DateTime)
    duration: Mapped[Float] = mapped_column(Float)
    user = relationship("User", back_populates="service_calls")
