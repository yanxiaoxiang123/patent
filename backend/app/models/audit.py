from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey, JSON, Index
from sqlalchemy.sql import func
from app.utils.database import Base


class AuditLog(Base):
    """管理员操作审计日志"""
    __tablename__ = "admin_audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="日志ID")
    operator_id = Column(Integer, nullable=False, comment="操作人ID")
    operator_username = Column(String(50), nullable=False, comment="操作人用户名")
    target_user_id = Column(Integer, nullable=True, comment="被操作用户ID")
    target_username = Column(String(50), nullable=True, comment="被操作用户名")
    action = Column(String(50), nullable=False, comment="操作类型: CREATE/DELETE/ENABLE/DISABLE/RESET_PWD/UPDATE/BATCH_DELETE/BATCH_ENABLE/BATCH_DISABLE")
    detail = Column(JSON, nullable=True, comment="详细信息")
    ip_address = Column(String(45), nullable=True, comment="操作IP")
    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        comment="操作时间"
    )

    __table_args__ = (
        Index("idx_operator_id", "operator_id"),
        Index("idx_target_user_id", "target_user_id"),
        Index("idx_action", "action"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', operator='{self.operator_username}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "operator_id": self.operator_id,
            "operator_username": self.operator_username,
            "target_user_id": self.target_user_id,
            "target_username": self.target_username,
            "action": self.action,
            "detail": self.detail,
            "ip_address": self.ip_address,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class LoginHistory(Base):
    """用户登录历史记录"""
    __tablename__ = "login_history"

    id = Column(Integer, primary_key=True, autoincrement=True, comment="记录ID")
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, comment="用户ID")
    ip_address = Column(String(45), nullable=True, comment="登录IP")
    user_agent = Column(String(512), nullable=True, comment="浏览器User-Agent")
    login_status = Column(String(20), default="success", nullable=False, comment="登录状态: success/failed")
    fail_reason = Column(String(255), nullable=True, comment="失败原因")
    created_at = Column(
        TIMESTAMP,
        server_default=func.now(),
        comment="登录时间"
    )

    __table_args__ = (
        Index("idx_user_id", "user_id"),
        Index("idx_created_at", "created_at"),
    )

    def __repr__(self):
        return f"<LoginHistory(id={self.id}, user_id={self.user_id}, status='{self.login_status}')>"

    def to_dict(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "ip_address": self.ip_address,
            "user_agent": self.user_agent,
            "login_status": self.login_status,
            "fail_reason": self.fail_reason,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }
