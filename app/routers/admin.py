# file: app/routers/admin.py

from typing import Annotated, List
from pydantic import BaseModel, Field, ValidationError
from fastapi import Depends, status, HTTPException, Path, APIRouter, Body
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import User
from ..schemas import ChangeUserAccessRights, ReadUser, CreateAdmin
from .auth import get_current_user, bcrypt_context

router = APIRouter(prefix='/admin', tags=['admin'])
    

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]    
    

############### ROUTES ###############
@router.get('/users', status_code=status.HTTP_200_OK, response_model=List[ReadUser])
async def get_all_users(user: user_dependency, db: db_dependency) -> list:
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return db.query(User).all()


@router.post('/create', status_code=status.HTTP_201_CREATED)
async def create_admin(
    db: db_dependency, create_user_request: CreateAdmin
) -> None:
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



@router.put('/users/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def change_user_access_rights(
    user: user_dependency, 
    db: db_dependency, 
    user_id: int = Path(gt=0),
    access_rights: ChangeUserAccessRights = Body(...),
) -> None:
    if user is None or user.get('role') != 'admin':
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    
    modified_user = db.query(User).filter(User.id == user_id).first()
    if modified_user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="User not found"
        )
    modified_user.is_active = access_rights.is_active
    modified_user.has_access_v1 = access_rights.has_access_v1
    modified_user.has_access_v2 = access_rights.has_access_v2  
    db.add(modified_user)
    db.commit()
    db.refresh(modified_user)
    



@router.delete('/users/{user_id}', status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user: user_dependency, 
    db: db_dependency,
    user_id: int = Path(gt=0)
) -> None:
    if user is None or user.get('role') != 'admin':
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Authentication failed')
        
    user_model = db.query(User).filter(User.id == user_id).delete()
    db.commit()