import logging
from fastapi import FastAPI
from sqladmin import Admin
from project.config import settings
from project.database import engine
from project.fu_core import api_router

logger = logging.getLogger(__name__)


def create_app() -> FastAPI:
    from project.logging import configure_logging
    configure_logging()
    
    app = FastAPI()

    from project.celery_utils import create_celery
    app.celery_app = create_celery()

    # @app.on_event("startup")
    # async def on_startup():
    #     from project.database import create_db_and_tables

    #     logger.info("creating the tables...")
    #     await create_db_and_tables()


    @app.get("/")
    async def root():
        return {"message": "hello world"}

    app.include_router(api_router, prefix=settings.API_V1_STR)

    # Add the UserAdmin view to the admin interface
    from project.sqladmin import UserAdmin
    admin = Admin(app, engine)
    admin.add_view(UserAdmin)

    return app
