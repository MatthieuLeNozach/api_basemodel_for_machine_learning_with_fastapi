# file: app/routers/auth.py

import os
from typing import Annotated, Optional
from datetime import datetime, timedelta
from pydantic import ValidationError

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from passlib.context import CryptContext
from jose import jwt, JWTError

from ..database import get_db
from ..models import User
from ..schemas import CreateUser, Token, TokenData

router = APIRouter(
    prefix='/auth',
    tags=['auth'])


SECRET_KEY = os.environ['SECRET_KEY']
ALGORITHM = 'HS256'

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')



############### DEPENDENCIES ###############
db_dependency = Annotated[Session, Depends(get_db)]
oauth2bearer = OAuth2PasswordBearer(tokenUrl='auth/token')



############### FUNCTIONS ###############
def authenticate_user(
    username: str, password: str, db
) -> Optional[User]:
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.hashed_password):
        return False
    
    return user


def create_access_token(token_data: TokenData) -> str:
    encode = token_data.dict()
    expires = datetime.utcnow() + token_data.expires_delta
    encode.update({'exp': expires})
    encode.pop('expires_delta', None)
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


async def get_current_user(
    token: Annotated[str, Depends(oauth2bearer)]
) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('username')
        user_id: int = payload.get('user_id')
        role: str = payload.get('role')
        has_access_v1: bool = payload.get('has_access_v1')
        has_access_v2: bool = payload.get('has_access_v2')

        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')
        return {
            'username': username,
            'id': user_id,
            'role': role,
            'has_access_v1': has_access_v1,
            'has_access_v2': has_access_v2
        }
    except jwt.JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate user')
    
    
    
############### ROUTES ###############
@router.post('/create', status_code=status.HTTP_201_CREATED)
async def create_user(
    db: db_dependency, create_user_request: CreateUser
) -> None:
    try:
        CreateUser.parse_obj(create_user_request.dict())
        password = create_user_request.password
        create_user_data = create_user_request.dict(exclude={"password"})
        create_user_data.update({
            "role": "user",
            "is_active": True,
            "has_access_v1": False,
            "has_access_v2": False
        })
        create_user_model = User(**create_user_data)
        create_user_model.hashed_password = bcrypt_context.hash(password)

        db.add(create_user_model)
        db.commit()

    except ValidationError as e:
        print(f"Validation Error: {e}")
        return {"detail": str(e)}



@router.post('/token', response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: db_dependency
) -> dict:
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Could not validate user'
        )
    
    token_data = TokenData(
        username=user.username,
        user_id=user.id,
        role=user.role,
        has_access_v1=user.has_access_v1,
        has_access_v2=user.has_access_v2,
        expires_delta=timedelta(minutes=20)
    )
    token = create_access_token(token_data)
    return {'access_token': token, 'token_type': 'bearer'}
    
    