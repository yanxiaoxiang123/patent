from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, Text, JSON
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.database import Base


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    title = Column(String(255))
    model = Column(String(50))
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"))
    last_message_at = Column(TIMESTAMP)
    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
    )
    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
    )

    user = relationship("User", back_populates="chat_sessions")
    document = relationship("Document", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"))
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    model = Column(String(50))
    token_count = Column(Integer)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="SET NULL"))
    extra = Column("metadata", JSON)
    message_index = Column(Integer, nullable=False)
    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
    )

    session = relationship("ChatSession", back_populates="messages")
    user = relationship("User")
    document = relationship("Document")
