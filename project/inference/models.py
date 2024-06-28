from project.database import Base
from sqlalchemy import (
    Boolean, 
    DateTime, 
    ForeignKey, 
    Integer, 
    String,
    text,
    UUID
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class AccessPolicy(Base):
    __tablename__ = "access_policy"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)
    daily_api_calls: Mapped[int] = mapped_column(Integer, default=1000, server_default="1000")
    monthly_api_calls: Mapped[int] = mapped_column(Integer, default=30000, server_default="30000")
    
    
    
class InferenceModel(Base):
    __tablename__ = "inference_model"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    problem: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str] = mapped_column(String, nullable=True)
    version: Mapped[str] = mapped_column(String, nullable=True)  # e.g., "1.0.0"
    first_deployed: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), nullable=False
    )
    last_updated: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'), nullable=False
    )
    deployment_status: Mapped[str] = mapped_column(
        String, nullable=False, default="Pending", server_default="Pending"
    ) 
    in_production: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False, server_default="False"
    )
    mlflow_id: Mapped[str] = mapped_column(String, nullable=True)
    source_url: Mapped[str] = mapped_column(String, nullable=True)
    access_policy_id: Mapped[int] = mapped_column(Integer, ForeignKey("access_policy.id"))
    
class UserAccess(Base):
    __tablename__ = "user_access"
    
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    model_id: Mapped[int] = mapped_column(Integer, ForeignKey("inference_model.id", ondelete="CASCADE"), primary_key=True)
    access_policy_id: Mapped[int] = mapped_column(Integer, ForeignKey("access_policy.id"), nullable=False)
    api_calls: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    access_granted: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_accessed: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'), onupdate=text('CURRENT_TIMESTAMP'), nullable=False)


class ServiceCall(Base):
    """Represents a service call made by a user."""
    
    __tablename__ = "service_call"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    model_id: Mapped[int] = mapped_column(Integer, ForeignKey("inference_model.id"))
    user_id: Mapped[UUID] = mapped_column(UUID, ForeignKey("user.id"))  # Ensure this is also UUID
    time_requested: Mapped[DateTime] = mapped_column(DateTime(timezone=True), server_default=text('CURRENT_TIMESTAMP'))
    time_completed: Mapped[DateTime] = mapped_column(DateTime(timezone=True), nullable=True)
    celery_task_id: Mapped[str] = mapped_column(String, nullable=True)