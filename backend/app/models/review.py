from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, JSON, DECIMAL
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from ..utils.database import Base


class ReviewRecord(Base):
    __tablename__ = "review_records"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="审核记录ID")
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False, comment="文档ID")
    review_type = Column(String(50), comment="审核类型: formal_check/logic_check")
    model_version = Column(String(50), comment="模型版本: qwen3-7b/coze-bot-v1")
    result_json = Column(JSON, comment="AI审核结果JSON")
    score = Column(Integer, comment="质量评分(0-100)")
    error_count = Column(Integer, default=0, comment="错误数量")
    processing_time = Column(DECIMAL(10, 3), comment="处理耗时(秒)")
    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        comment="创建时间"
    )

    # 关联关系
    document = relationship("Document", back_populates="review_records")

    def __repr__(self):
        return f"<ReviewRecord(id={self.id}, type='{self.review_type}', score={self.score})>"

    def to_dict(self):
        return {
            "id": self.id,
            "document_id": self.document_id,
            "review_type": self.review_type,
            "model_version": self.model_version,
            "result_json": self.result_json,
            "score": self.score,
            "error_count": self.error_count,
            "processing_time": float(self.processing_time) if self.processing_time else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }