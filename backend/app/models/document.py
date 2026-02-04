from sqlalchemy import Column, Integer, String, TIMESTAMP, BigInteger, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.utils.database import Base


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="文档ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    title = Column(String(255), comment="文档标题")
    file_path = Column(String(512), nullable=False, comment="文件存储路径")
    file_type = Column(String(10), comment="文件类型: pdf/docx")
    file_size = Column(BigInteger, comment="文件大小(字节)")
    parsed_content = Column(JSON, comment="解析后的结构化内容")
    status = Column(String(20), default="uploaded", nullable=False, comment="状态: uploaded/parsing/reviewed/completed")
    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        comment="创建时间"
    )
    updated_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        onupdate=func.now(),
        comment="更新时间"
    )

    user = relationship("User", back_populates="documents")
    review_records = relationship("ReviewRecord", back_populates="document", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="document")

    def __repr__(self):
        return f"<Document(id={self.id}, title='{self.title}', status='{self.status}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "title": self.title,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "status": self.status,
            "parsed_content": self.parsed_content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }
