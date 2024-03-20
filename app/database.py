# file: app/database.py

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base



SQLALCHEMY_DATABASE_URL = os.environ['SQL_URL']

# base create_engine, uncomment next line for sql servers postgresql, mysql etc.
# engine = create_engine(SQLALCHEMY_DATABASE_URL)

# add connect_args={'check_same_thread': False} when using sqlite
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={'check_same_thread': False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
