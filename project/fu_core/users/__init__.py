import uuid
from typing import Optional

from fastapi import Request
from fastapi_users import BaseUserManager, FastAPIUsers, UUIDIDMixin

from project.config import settings
from project.fu_core.security import auth_backend
from project.fu_core.users import deps, models


class UserManager(UUIDIDMixin, BaseUserManager[models.User, uuid.UUID]):
    reset_password_token_secret = settings.SECRET_KEY
    verification_token_secret = settings.SECRET_KEY

    async def on_after_register(self, user: models.User, request: Optional[Request] = None):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self, user: models.User, token: str, request: Optional[Request] = None
    ):
        print(f"User {user.id} has forgot their password. Reset token: {token}")

    async def on_after_request_verify(
        self, user: models.User, token: str, request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}. Verification token: {token}")


fastapi_users = FastAPIUsers[models.User, uuid.UUID](deps.get_user_manager, [auth_backend])

current_active_user = fastapi_users.current_user(active=True)
current_superuser = fastapi_users.current_user(active=True, superuser=True)