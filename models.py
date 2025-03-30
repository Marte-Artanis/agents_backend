from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, Date, MetaData, Index, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from config import APP_CONFIG

# Cria o metadata para o schema específico do Supabase
metadata = MetaData(schema=APP_CONFIG['DB_SCHEMA'])
Base = declarative_base(metadata=metadata)

class User(Base):
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    first_name = Column(String(100), nullable=False)
    last_name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    birth_date = Column(Date, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # Relacionamentos
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    chat_history = relationship("ChatHistory", back_populates="user", cascade="all, delete-orphan")

    # Índices
    __table_args__ = (
        Index('idx_users_email', 'email'),
    )

class Session(Base):
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    token = Column(String(255), nullable=False)
    is_active = Column(Boolean, nullable=False, default=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relacionamentos
    user = relationship("User", back_populates="sessions")

    # Índices
    __table_args__ = (
        Index('idx_sessions_token', 'token'),
        Index('idx_sessions_user_id', 'user_id'),
    )

class ChatHistory(Base):
    __tablename__ = 'chat_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    session_id = Column(String(255), nullable=False)
    character_name = Column(String(255), nullable=False)
    user_input = Column(Text, nullable=False)
    response = Column(Text, nullable=False)
    context = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relacionamentos
    user = relationship("User", back_populates="chat_history")

    # Índices
    __table_args__ = (
        Index('idx_chat_history_user_id', 'user_id'),
        Index('idx_chat_history_session_id', 'session_id'),
        Index('idx_chat_history_character', 'character_name'),
        Index('idx_chat_history_created_at', 'created_at'),
    ) 