#file: app/models.py

from sqlalchemy import Column, Float, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

class User(Base):
    __tablename__ = 'users'
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(127), unique=True)
    first_name: Mapped[str] = mapped_column(String(127))
    last_name: Mapped[str] = mapped_column(String(127))
    country: Mapped[str] = mapped_column(String(127), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
    role: Mapped[str] = mapped_column(String(255))
    has_access_v1: Mapped[bool] = mapped_column(Boolean, default=False)
    has_access_v2: Mapped[bool] = mapped_column(Boolean, default=False)
    service_calls = relationship('ServiceCall', back_populates='user')
    
    
class ServiceCall(Base):
    __tablename__ = 'service_calls'
    
    id: Mapped[str] = mapped_column(Integer, primary_key=True, index=True)
    service_version: Mapped[str] = mapped_column(String(2))
    #priority: Mapped[int] = mapped_column(Integer)
    success: Mapped[bool] = mapped_column(Boolean, default=False)
    owner_id: Mapped[int] = mapped_column(Integer, ForeignKey('users.id'))
    request_time: Mapped[DateTime] = mapped_column(DateTime, default=func.now())
    completion_time: Mapped[DateTime] = mapped_column(DateTime)
    duration: Mapped[Float] = mapped_column(Float)
    user = relationship('User', back_populates='service_calls')

    

