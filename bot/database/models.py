"""SQLAlchemy модели базы данных"""
from datetime import datetime
from sqlalchemy import BigInteger, Integer, String, Text, DateTime, ForeignKey, JSON, UniqueConstraint, Index, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from bot.database.engine import Base


class AllowedUser(Base):
    """Модель белого списка пользователей"""
    __tablename__ = "allowed_users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram ID
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)  # Полное имя
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class User(Base):
    """Модель пользователя"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)  # Telegram ID
    role: Mapped[str] = mapped_column(String(20), nullable=False)  # employee, warehouseman, manager
    active_role: Mapped[str | None] = mapped_column(String(20), nullable=True)  # Активная роль для менеджера (employee, warehouseman, или None для базовой роли)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True)
    first_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    language_code: Mapped[str | None] = mapped_column(String(16), nullable=True)
    is_premium: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    first_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    requests: Mapped[list["Request"]] = relationship("Request", back_populates="user", cascade="all, delete-orphan")
    complaints: Mapped[list["Complaint"]] = relationship("Complaint", back_populates="user", cascade="all, delete-orphan")


class Request(Base):
    """Модель заявки"""
    __tablename__ = "requests"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, index=True)
    number: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)  # ЗХ-ДДММГГ-№№№
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    category: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    quantity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    priority: Mapped[str] = mapped_column(String(10), nullable=False)  # normal, urgent
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="new", index=True)  # new, in_progress, completed, rejected
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="requests")
    photos: Mapped[list["RequestPhoto"]] = relationship("RequestPhoto", back_populates="request", cascade="all, delete-orphan")


class RequestPhoto(Base):
    """Модель фото заявки"""
    __tablename__ = "request_photos"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey("requests.id"), nullable=False, index=True)
    file_id: Mapped[str] = mapped_column(String(200), nullable=False)  # Telegram file_id
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    request: Mapped["Request"] = relationship("Request", back_populates="photos")


class WarehouseItem(Base):
    """Модель позиции на складе"""
    __tablename__ = "warehouse_items"
    __table_args__ = (
        UniqueConstraint("tenant_id", "name", name="uq_warehouse_items_tenant_name"),
        Index("ix_warehouse_items_tenant_name", "tenant_id", "name"),
    )
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, index=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    current_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Complaint(Base):
    """Модель жалобы"""
    __tablename__ = "complaints"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, index=True)
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey("requests.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="complaints")
    request: Mapped["Request"] = relationship("Request")


class UserEvent(Base):
    """События пользователя (маркетинг/аналитика/аудит)"""
    __tablename__ = "user_events"
    __table_args__ = (
        Index("ix_user_events_tenant_created", "tenant_id", "created_at"),
        Index("ix_user_events_user_created", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    event_type: Mapped[str] = mapped_column(String(64), nullable=False, index=True)  # start, role_switch, etc
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class TechnicianAssignment(Base):
    """Назначение техника руководителю (в DEMO режиме)"""
    __tablename__ = "technician_assignments"
    __table_args__ = (
        UniqueConstraint("manager_id", "technician_id", name="uq_technician_assignments_manager_technician"),
        Index("ix_technician_assignments_manager", "manager_id"),
        Index("ix_technician_assignments_technician", "technician_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    manager_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)  # ID руководителя (tenant_id)
    technician_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)  # ID техника (Telegram ID)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    
    # Relationships
    manager: Mapped["User"] = relationship("User", foreign_keys=[manager_id])
    technician: Mapped["User"] = relationship("User", foreign_keys=[technician_id])

