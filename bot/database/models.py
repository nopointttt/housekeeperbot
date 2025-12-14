"""SQLAlchemy модели базы данных"""
from datetime import datetime
from sqlalchemy import BigInteger, Integer, String, Text, DateTime, ForeignKey, JSON
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
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    requests: Mapped[list["Request"]] = relationship("Request", back_populates="user", cascade="all, delete-orphan")
    complaints: Mapped[list["Complaint"]] = relationship("Complaint", back_populates="user", cascade="all, delete-orphan")


class Request(Base):
    """Модель заявки"""
    __tablename__ = "requests"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
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
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False, unique=True)
    current_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    min_quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class Complaint(Base):
    """Модель жалобы"""
    __tablename__ = "complaints"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    request_id: Mapped[int] = mapped_column(Integer, ForeignKey("requests.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(BigInteger, ForeignKey("users.id"), nullable=False, index=True)
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="complaints")
    request: Mapped["Request"] = relationship("Request")

