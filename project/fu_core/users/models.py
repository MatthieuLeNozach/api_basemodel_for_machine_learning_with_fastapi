from fastapi_users.db import SQLAlchemyBaseUserTableUUID

from project.database import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    pass
