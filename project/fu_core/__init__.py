from fastapi import APIRouter, Depends

from project.fu_core.security import auth_backend
from project.fu_core.users import current_active_user, fastapi_users, schemas
from project.fu_core.users.models import User

fastapi_users_router = APIRouter()

fastapi_users_router.include_router(
    fastapi_users.get_auth_router(auth_backend), prefix="/auth/jwt", tags=["auth"]
)
fastapi_users_router.include_router(
    fastapi_users.get_register_router(schemas.UserRead, schemas.UserCreate),
    prefix="/auth",
    tags=["auth"],
)
fastapi_users_router.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"],
)
fastapi_users_router.include_router(
    fastapi_users.get_verify_router(schemas.UserRead),
    prefix="/auth",
    tags=["auth"],
)
fastapi_users_router.include_router(
    fastapi_users.get_users_router(schemas.UserRead, schemas.UserUpdate),
    prefix="/users",
    tags=["users"],
)

@fastapi_users_router.get("/authenticated-route")
async def authenticated_route(user: User = Depends(current_active_user)):
    return {"message": f"Hello {user.email}!"}
