import os
import pathlib
import secrets
from functools import lru_cache
from typing import ClassVar
from kombu import Queue

def route_task(name, args, kwargs, options, task=None, **kw):
    if ":" in name:
        queue, _ = name.split(":")
        return {"queue": queue}
    return {"queue": "default"}


class BaseConfig:
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_TOKEN_LIFETIME: int = 3600

    BASE_DIR: pathlib.Path = pathlib.Path(__file__).parent.parent
    UPLOAD_DEFAULT_DEST: ClassVar[str] = str(BASE_DIR / "upload")

    # Construct DATABASE_URL using environment variables
    DB_USER = os.environ.get("POSTGRES_USER", "postgres")
    DB_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
    DB_HOST = os.environ.get("POSTGRES_HOST", "localhost")
    DB_PORT = os.environ.get("POSTGRES_PORT", "5432")
    DB_NAME = os.environ.get("POSTGRES_DB", "postgres")

    DATABASE_URL: ClassVar[str] = (
        f"postgresql+asyncpg://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    DATABASE_CONNECT_DICT: ClassVar[dict] = {}

    CELERY_BROKER_URL: str = os.environ.get("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
    CELERY_RESULT_BACKEND: str = os.environ.get("CELERY_RESULT_BACKEND", "redis://127.0.0.1:6379/0")

    CELERY_TASK_DEFAULT_QUEUE: str = "default"
    CELERY_TASK_CREATE_MISSING_QUEUES: bool = False

    CELERY_TASK_QUEUES: list = (
        Queue("default"), # type: ignore
        Queue("high_priority"), # type: ignore
        Queue("low_priority") # type: ignore
    )
    CELERY_TASK_ROUTES = {
        "project.users.tasks.*": {
            "queue": "high_priority",
        },
    }
    CELERY_TASK_ROUTES = (route_task,)

    # Define your Celery beat schedule here
    CELERY_BEAT_SCHEDULE: dict = {
        "dummy_task": {
            "task": "project.celery_utils.dummy_task",
            "schedule": 60.0  # Run every 60 seconds
        },
    }



class DevelopmentConfig(BaseConfig):
    pass


class ProductionConfig(BaseConfig):
    pass


class TestingConfig(BaseConfig):
    # https://fastapi.tiangolo.com/advanced/testing-database/
    DATABASE_URL: ClassVar[str] = "sqlite+aiosqlite:///./test.db"
    DATABASE_CONNECT_DICT: ClassVar[dict] = {"check_same_thread": False}


@lru_cache
def get_settings():
    config_cls_dict = {
        "development": DevelopmentConfig,
        "production": ProductionConfig,
        "testing": TestingConfig,
    }

    config_name = os.environ.get("FASTAPI_CONFIG", "development")
    config_cls = config_cls_dict[config_name]
    return config_cls


settings = get_settings()
