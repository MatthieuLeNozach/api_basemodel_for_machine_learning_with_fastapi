# file: app/dev_tools.py

from sqlalchemy.orm import Session
from .models import User
from passlib.context import CryptContext

    
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_superuser(db: Session):
    superuser = User(
        username='superuser@example.com',
        first_name='Super',
        last_name='User',
        hashed_password=pwd_context.hash('8888'),
        is_active=True,
        role='admin',
        has_access_v1=True,
        has_access_v2=True
    )
    db.add(superuser)
    db.commit()

def remove_superuser(db: Session):
    db.query(User).filter(User.username == 'superuser@example.com').delete()
    db.commit()
    
    
    
