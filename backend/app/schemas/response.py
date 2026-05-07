"""统一 API 响应格式模块"""
import logging
from typing import Any, Optional, TypeVar, Generic
from pydantic import BaseModel

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    """统一 API 响应格式"""
    success: bool
    data: Optional[T] = None
    error: Optional[str] = None
    meta: Optional[dict] = None  # 分页等信息
    message: Optional[str] = None  # 操作提示

    @classmethod
    def ok(cls, data: T = None, message: str = None, meta: dict = None) -> "ApiResponse[T]":
        """成功响应"""
        return cls(success=True, data=data, error=None, message=message, meta=meta)

    @classmethod
    def fail(cls, error: str, data: T = None) -> "ApiResponse[T]":
        """失败响应"""
        return cls(success=False, data=data, error=error, message=None, meta=None)


def wrap_response(data: Any, error: str = None) -> dict:
    """将数据包装为统一响应格式（兼容非 Pydantic 返回值）"""
    if error:
        return {"success": False, "data": None, "error": error}
    return {"success": True, "data": data, "error": None}
