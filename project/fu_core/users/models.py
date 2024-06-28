from fastapi_users.db import SQLAlchemyBaseUserTableUUID
from sqlalchemy import DateTime, text
from sqlalchemy.orm import Mapped, mapped_column


from project.database import Base


class User(SQLAlchemyBaseUserTableUUID, Base):
    date_created: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), nullable=False)
    date_deleted: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)


