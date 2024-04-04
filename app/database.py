# file: app/database.py
"""
Module: database.py

This module provides the database configuration and setup for the application.
It uses SQLAlchemy as the ORM (Object-Relational Mapping) library to interact
with the database.

The module includes the following main components:

- `SQLALCHEMY_DATABASE_URL`: The database connection URL obtained from the environment variable "SQL_URL".
- `engine`: The SQLAlchemy engine instance created based on the database URL.
- `SessionLocal`: The sessionmaker factory used to create database sessions.
- `Base`: The declarative base class for defining database models.
- `get_db`: A dependency function that yields a database session for each request.

To use a different database system (e.g., PostgreSQL, MySQL), uncomment the appropriate
`create_engine` line and modify the connection URL accordingly.

When using SQLite, the `connect_args` parameter is set to `{"check_same_thread": False}`
to allow multiple threads to access the database concurrently.

The `get_db` function is used as a dependency in FastAPI routes to provide a database
session to the route handlers. It ensures that the session is properly closed after
each request.
"""
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base


SQLALCHEMY_DATABASE_URL = os.getenv("SQL_URL")

# base create_engine, uncomment next line for sql servers postgresql, mysql etc.
# engine = create_engine(SQLALCHEMY_DATABASE_URL)

# add connect_args={'check_same_thread': False} when using sqlite
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    """
    Dependency function to get a database session.

    Yields:
        db (Session): A database session.

    Notes:
        - This function is used as a dependency in FastAPI routes to provide a database session.
        - It creates a new database session using `SessionLocal` and yields it.
        - The session is automatically closed after the request is processed.

    Example usage:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
