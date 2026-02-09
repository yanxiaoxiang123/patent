"""自定义异常模块"""
import logging
from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


class AppException(Exception):
    """应用基础异常类"""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)


class AuthenticationException(AppException):
    """认证异常"""
    def __init__(self, message: str = "认证失败"):
        super().__init__(message, status_code=401)


class AuthorizationException(AppException):
    """授权异常"""
    def __init__(self, message: str = "权限不足"):
        super().__init__(message, status_code=403)


class NotFoundException(AppException):
    """资源不存在异常"""
    def __init__(self, message: str = "资源不存在"):
        super().__init__(message, status_code=404)


class DatabaseException(AppException):
    """数据库异常"""
    def __init__(self, message: str = "数据库操作失败"):
        super().__init__(message, status_code=500)


class AIServiceException(AppException):
    """AI 服务异常"""
    def __init__(self, message: str = "AI 服务不可用"):
        super().__init__(message, status_code=503)


async def app_exception_handler(request: Request, exc: AppException):
    """应用异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误"}
    )
