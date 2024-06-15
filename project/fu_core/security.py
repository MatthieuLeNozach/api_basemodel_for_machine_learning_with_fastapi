from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from project.config import settings

bearer_transport = BearerTransport(tokenUrl=f"{settings.API_V1_STR}/auth/jwt/login")


def get_jwt_strategy() -> JWTStrategy:
    return JWTStrategy(
        secret=settings.SECRET_KEY, lifetime_seconds=settings.JWT_TOKEN_LIFETIME, algorithm="HS256"
    )


auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)
