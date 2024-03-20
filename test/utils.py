# file: test/utils.py
import os
from dotenv import load_dotenv

# Load shared environment variables
load_dotenv('.environment/.env.shared')
load_dotenv(dotenv_path='.environment/.env.test', override=True)

from fastapi.testclient import TestClient
from fastapi import status


from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from ..app.main import app
from ..app.routers.auth import bcrypt_context
from ..app.database import Base
from ..app.models import User

import pytest

# Retrieve the SQL_URL from the environment variables
SQL_URL = os.getenv('SQL_URL')
if not SQL_URL:
    raise ValueError("SQL_URL environment variable not set")

# Create the engine with the retrieved SQL_URL
engine = create_engine(
    SQL_URL,
    connect_args={'check_same_thread': False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        

def override_get_current_user():
    return {'username': 'testy_mc_testface@example.com', 
            'id': 1, 
            'role': 'admin',
            'has_access_v1': True,
            'has_access_v2': True
    }
    

def override_get_current_user_revoked():
    return {
        'username': 'banny_mc_banface@example.com',
        'id': 2,
        'role': 'user',
        'has_access_v1': False,
        'has_access_v2': False
    }


client = TestClient(app)


###################### FIXTURES ########################
@pytest.fixture(scope='session', autouse=True)
def reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def test_superuser():
    user = User(
        username='testy_mc_testface@example.com',
        first_name='Testy',
        last_name='McTestface',
        hashed_password=bcrypt_context.hash('8888'),
        role='admin',
        country='UK',
        has_access_v1=True,
        has_access_v2=True,
    )
    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    yield user
    with engine.connect() as connection:
        connection.execute(text('DELETE FROM users;'))
        connection.commit()


@pytest.fixture
def test_user_revoked():
    user = User(
        username='banny_mc_banface@example.com',
        first_name='Banny',
        last_name='McBanface',
        hashed_password=bcrypt_context.hash('8888'),
        role='admin',
        country='UK',
        has_access_v1=False,
        has_access_v2=False,
    )
    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    yield user
    with engine.connect() as connection:
        connection.execute(text('DELETE FROM users;'))
        connection.commit()


@pytest.fixture
def test_regular_users_granted():
    users = []
    db = TestingSessionLocal()
    try:
        for i in range(4):
            user = User(
                username=f'user{i}@example.com',
                first_name=f'FirstNameUser{i}',
                last_name=f'LastNameUser{i}',
                hashed_password=bcrypt_context.hash('8888'),
                role='user',
                country='DE',
                is_active=True,
                has_access_v1=True,
                has_access_v2=True
            )
            db.add(user)
            users.append(user)

        db.commit()
        yield users
        
    finally:
        with engine.connect() as connection:
            connection.execute(text('DELETE FROM users;'))
            connection.commit()
        db.close()



@pytest.fixture
def test_regular_users_revoked(request):
    num_users = request.param if hasattr(request, 'param') else 4
    users = []
    db = TestingSessionLocal()
    try:
        for i in range(num_users):
            user = User(
                username=f'user{i}@example.com',
                first_name=f'FirstNameUser{i}',
                last_name=f'LastNameUser{i}',
                hashed_password=bcrypt_context.hash('8888'),
                role='user',
                country='DE',
                is_active=False,
                has_access_v1=False,
                has_access_v2=False
            )
            db.add(user)
            users.append(user)

        db.commit()
        yield users
        
    finally:
        with engine.connect() as connection:
            connection.execute(text('DELETE FROM users;'))
            connection.commit()
        db.close()


