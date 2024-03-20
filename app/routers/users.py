# file: users.py

from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import APIRouter, status, HTTPException, Depends
from passlib.context import CryptContext

from ..models import User
from ..schemas import UserVerification, ReadUser
from ..database import get_db
from .auth import get_current_user

router = APIRouter(prefix='/user', tags=['user'])

############### DEPENDENCIES ###############
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')




############### ROUTES ###############
@router.get('/', status_code=status.HTTP_200_OK, response_model=ReadUser)
async def get_user(user: user_dependency, db: db_dependency) -> User:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Authentication failed'
        )
    return db.query(User).filter(User.id == user.get('id')).first()


@router.put('/password', status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    user: user_dependency, db: db_dependency, user_verification: UserVerification
) -> None:
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Authentication failed'
        )
    
    user_model = db.query(User).filter(User.id == user.get('id')).first()
    if not bcrypt_context.verify(user_verification.password, user_model.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Error on password change'
        )
    user_model.hashed_password = bcrypt_context.hash(user_verification.new_password)
    db.add(user_model)
    db.commit()