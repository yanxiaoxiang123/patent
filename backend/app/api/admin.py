"""管理员 API 模块"""
import csv
import logging
from datetime import datetime, timedelta
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Request, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy import select, func, and_, or_

from app.core.security import parse_auth_header
from app.core.exceptions import AuthenticationException, AuthorizationException
from app.services.user_repository import UserRepository
from app.utils.database import AsyncSessionLocal
from app.utils.passwords import hash_password, verify_password
from app.models import User as UserModel, AuditLog, LoginHistory, Document, ChatSession

logger = logging.getLogger(__name__)
router = APIRouter(tags=["管理员管理"])


# ===================== Helper Functions =====================

def get_client_ip(request: Request) -> str:
    """Extract client IP from request"""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    if request.client:
        return request.client.host
    return "unknown"


async def create_audit_log(
    session,
    operator_id: int,
    operator_username: str,
    action: str,
    ip_address: str,
    target_user_id: Optional[int] = None,
    target_username: Optional[str] = None,
    detail: Optional[dict] = None
):
    """Create an audit log entry"""
    audit_log = AuditLog(
        operator_id=operator_id,
        operator_username=operator_username,
        action=action,
        ip_address=ip_address,
        target_user_id=target_user_id,
        target_username=target_username,
        detail=detail
    )
    session.add(audit_log)
    await session.commit()


# ===================== Pydantic Models =====================

class UserCreate(BaseModel):
    """创建用户请求"""
    username: str = Field(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')
    password: str = Field(min_length=6, max_length=100)
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str = Field(default="user", pattern=r'^(admin|user)$')


class UserUpdate(BaseModel):
    """更新用户请求"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=6, max_length=100)
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: Optional[str] = Field(None, pattern=r'^(admin|user)$')


class UserResponse(BaseModel):
    """用户响应"""
    id: int
    username: str
    role: str
    email: Optional[str]
    full_name: Optional[str]
    is_active: bool
    last_login_at: Optional[str]
    last_login_ip: Optional[str]
    login_attempts: int
    created_at: Optional[str]


class BatchIdsRequest(BaseModel):
    """批量操作请求"""
    user_ids: List[int] = Field(min_length=1, description="用户ID列表")


class BatchToggleStatusRequest(BaseModel):
    """批量切换状态请求"""
    user_ids: List[int] = Field(min_length=1, description="用户ID列表")
    enable: bool = Field(description="true: 启用, false: 禁用")


class BatchResetPasswordRequest(BaseModel):
    """批量重置密码请求"""
    user_ids: List[int] = Field(min_length=1, description="用户ID列表")
    password: str = Field(min_length=6, max_length=100, description="新密码")


class ResetPasswordRequest(BaseModel):
    """单个用户重置密码请求"""
    password: str = Field(min_length=6, max_length=100, description="新密码")


# ===================== 认证依赖 =====================

async def get_current_user(request: Request) -> dict:
    """获取当前用户"""
    from app.core.security import TokenPayload
    token_payload: Optional[TokenPayload] = parse_auth_header(request.headers.get("Authorization"))
    if not token_payload:
        raise AuthenticationException("未认证或Token已过期")

    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, token_payload.user_id)

    if not user:
        raise AuthenticationException("用户不存在")

    if token_payload.username != user.username:
        raise AuthenticationException("用户信息已变更，请重新登录")

    return {
        "id": str(user.id),
        "username": user.username,
        "role": user.role or "user"
    }


async def require_admin(request: Request) -> dict:
    """管理员权限校验"""
    user = await get_current_user(request)
    if user.get("role") != "admin":
        raise AuthorizationException("需要管理员权限")
    return user


# ===================== 管理员路由 =====================

@router.get("/users")
async def list_users(
    request: Request,
    current_admin: dict = Depends(require_admin),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    search: Optional[str] = Query(None, description="搜索用户名"),
    role: Optional[str] = Query(None, pattern=r'^(admin|user)$', description="角色筛选"),
    activity_status: Optional[str] = Query(None, pattern=r'^(active_7d|active_30d|never_login)$', description="活动状态筛选")
):
    """获取用户列表（支持分页、搜索、筛选、活动状态筛选）"""
    async with AsyncSessionLocal() as session:
        query = select(UserModel)

        # 搜索条件
        if search:
            query = query.where(UserModel.username.like(f"%{search}%"))

        # 角色筛选
        if role:
            query = query.where(UserModel.role == role)

        # 活动状态筛选
        if activity_status:
            now = datetime.utcnow()
            if activity_status == "active_7d":
                threshold = now - timedelta(days=7)
                query = query.where(UserModel.last_login_at >= threshold)
            elif activity_status == "active_30d":
                threshold = now - timedelta(days=30)
                query = query.where(UserModel.last_login_at >= threshold)
            elif activity_status == "never_login":
                query = query.where(UserModel.last_login_at.is_(None))

        # 获取总数
        count_query = select(func.count(UserModel.id))
        if search:
            count_query = count_query.where(UserModel.username.like(f"%{search}%"))
        if role:
            count_query = count_query.where(UserModel.role == role)
        if activity_status:
            now = datetime.utcnow()
            if activity_status == "active_7d":
                threshold = now - timedelta(days=7)
                count_query = count_query.where(UserModel.last_login_at >= threshold)
            elif activity_status == "active_30d":
                threshold = now - timedelta(days=30)
                count_query = count_query.where(UserModel.last_login_at >= threshold)
            elif activity_status == "never_login":
                count_query = count_query.where(UserModel.last_login_at.is_(None))

        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * size
        query = query.offset(offset).limit(size)

        result = await session.execute(query)
        users_model = list(result.scalars().all())

        users = []
        for user in users_model:
            users.append({
                "id": user.id,
                "username": user.username,
                "role": user.role,
                "email": user.email,
                "full_name": user.full_name,
                "is_active": user.is_active,
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                "last_login_ip": user.last_login_ip,
                "login_attempts": user.login_attempts,
                "created_at": user.created_at.isoformat() if user.created_at else None
            })

        return {
            "data": users,
            "total": total,
            "page": page,
            "size": size,
        }


@router.post("/users")
async def create_user(request: Request, payload: UserCreate, current_admin: dict = Depends(require_admin)):
    """创建用户"""
    ip_address = get_client_ip(request)

    async with AsyncSessionLocal() as session:
        # 检查用户名是否存在
        exists = await UserRepository.username_exists(session, payload.username)
        if exists:
            raise HTTPException(status_code=400, detail="用户名已存在")

        hashed = hash_password(payload.password)

        user = await UserRepository.create(
            session,
            username=payload.username,
            password_hash=hashed,
            email=payload.email,
            full_name=payload.full_name,
            role=payload.role
        )

        # 审计日志
        await create_audit_log(
            session=session,
            operator_id=int(current_admin["id"]),
            operator_username=current_admin["username"],
            action="CREATE",
            ip_address=ip_address,
            target_user_id=user.id,
            target_username=user.username,
            detail={"role": user.role, "email": user.email}
        )

        return {
            "message": "创建成功",
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }


@router.get("/users/{user_id}")
async def get_user(user_id: int, current_admin: dict = Depends(require_admin)):
    """获取单个用户"""
    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        return {
            "id": user.id,
            "username": user.username,
            "role": user.role,
            "email": user.email,
            "full_name": user.full_name,
            "is_active": user.is_active,
            "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
            "last_login_ip": user.last_login_ip,
            "login_attempts": user.login_attempts,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }


@router.put("/users/{user_id}")
async def update_user(request: Request, user_id: int, payload: UserUpdate, current_admin: dict = Depends(require_admin)):
    """更新用户"""
    ip_address = get_client_ip(request)

    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 如果要修改用户名，检查是否重复
        if payload.username and payload.username != user.username:
            exists = await UserRepository.username_exists(session, payload.username)
            if exists:
                raise HTTPException(status_code=400, detail="用户名已存在")

        # 更新字段
        update_data = payload.model_dump(exclude_unset=True)
        if "password" in update_data:
            update_data["password_hash"] = hash_password(update_data.pop("password"))

        old_values = {}
        for field, value in update_data.items():
            old_values[field] = getattr(user, field)
            setattr(user, field, value)

        await session.commit()

        # 审计日志
        await create_audit_log(
            session=session,
            operator_id=int(current_admin["id"]),
            operator_username=current_admin["username"],
            action="UPDATE",
            ip_address=ip_address,
            target_user_id=user.id,
            target_username=user.username,
            detail={"old": old_values, "new": update_data}
        )

        return {
            "message": "更新成功",
            "user_id": user.id,
            "username": user.username,
            "role": user.role
        }


@router.delete("/users/{user_id}")
async def delete_user(request: Request, user_id: int, current_admin: dict = Depends(require_admin)):
    """删除用户"""
    ip_address = get_client_ip(request)

    # 不能删除自己
    if int(current_admin["id"]) == user_id:
        raise HTTPException(status_code=400, detail="不能删除当前登录的管理员账户")

    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        username = user.username
        success = await UserRepository.delete(session, user_id)

        if success:
            # 审计日志
            await create_audit_log(
                session=session,
                operator_id=int(current_admin["id"]),
                operator_username=current_admin["username"],
                action="DELETE",
                ip_address=ip_address,
                target_user_id=user_id,
                target_username=username
            )

        return {"message": "删除成功"}


@router.post("/users/{user_id}/reset-password")
async def reset_password(request: Request, user_id: int, payload: ResetPasswordRequest, current_admin: dict = Depends(require_admin)):
    """重置用户密码"""
    ip_address = get_client_ip(request)

    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        user.password_hash = hash_password(payload.password)
        await session.commit()

        # 审计日志
        await create_audit_log(
            session=session,
            operator_id=int(current_admin["id"]),
            operator_username=current_admin["username"],
            action="RESET_PWD",
            ip_address=ip_address,
            target_user_id=user.id,
            target_username=user.username
        )

        return {"message": "密码重置成功"}


@router.patch("/users/{user_id}/toggle-status")
async def toggle_user_status(request: Request, user_id: int, current_admin: dict = Depends(require_admin)):
    """切换用户启用/禁用状态"""
    ip_address = get_client_ip(request)

    # 不能操作自己
    if int(current_admin["id"]) == user_id:
        raise HTTPException(status_code=400, detail="不能修改当前登录账户的状态")

    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        user.is_active = not user.is_active
        await session.commit()

        action = "ENABLE" if user.is_active else "DISABLE"

        # 审计日志
        await create_audit_log(
            session=session,
            operator_id=int(current_admin["id"]),
            operator_username=current_admin["username"],
            action=action,
            ip_address=ip_address,
            target_user_id=user.id,
            target_username=user.username,
            detail={"is_active": user.is_active}
        )

        status_text = "启用" if user.is_active else "禁用"
        return {"message": f"用户已{status_text}", "is_active": user.is_active}


# ===================== Batch Operations =====================

@router.post("/users/batch-delete")
async def batch_delete_users(request: Request, payload: BatchIdsRequest, current_admin: dict = Depends(require_admin)):
    """批量删除用户"""
    ip_address = get_client_ip(request)
    current_admin_id = int(current_admin["id"])

    # 不能删除自己
    if current_admin_id in payload.user_ids:
        raise HTTPException(status_code=400, detail="不能删除当前登录的管理员账户")

    deleted_count = 0
    failed_users = []

    async with AsyncSessionLocal() as session:
        for user_id in payload.user_ids:
            if user_id == current_admin_id:
                failed_users.append({"user_id": user_id, "reason": "不能删除自己"})
                continue

            user = await UserRepository.get_by_id(session, user_id)
            if not user:
                failed_users.append({"user_id": user_id, "reason": "用户不存在"})
                continue

            username = user.username
            success = await UserRepository.delete(session, user_id)
            if success:
                deleted_count += 1
                # 审计日志
                await create_audit_log(
                    session=session,
                    operator_id=current_admin_id,
                    operator_username=current_admin["username"],
                    action="BATCH_DELETE",
                    ip_address=ip_address,
                    target_user_id=user_id,
                    target_username=username
                )
            else:
                failed_users.append({"user_id": user_id, "reason": "删除失败"})

    return {
        "message": f"批量删除完成，成功删除 {deleted_count} 个用户",
        "deleted_count": deleted_count,
        "failed_users": failed_users if failed_users else None
    }


@router.post("/users/batch-toggle-status")
async def batch_toggle_status(request: Request, payload: BatchToggleStatusRequest, current_admin: dict = Depends(require_admin)):
    """批量启用/禁用用户"""
    ip_address = get_client_ip(request)
    current_admin_id = int(current_admin["id"])

    # 不能操作自己
    if current_admin_id in payload.user_ids:
        raise HTTPException(status_code=400, detail="不能修改当前登录账户的状态")

    updated_count = 0
    failed_users = []
    action = "BATCH_ENABLE" if payload.enable else "BATCH_DISABLE"

    async with AsyncSessionLocal() as session:
        for user_id in payload.user_ids:
            if user_id == current_admin_id:
                failed_users.append({"user_id": user_id, "reason": "不能操作自己"})
                continue

            user = await UserRepository.get_by_id(session, user_id)
            if not user:
                failed_users.append({"user_id": user_id, "reason": "用户不存在"})
                continue

            user.is_active = payload.enable
            await session.commit()

            updated_count += 1
            # 审计日志
            await create_audit_log(
                session=session,
                operator_id=current_admin_id,
                operator_username=current_admin["username"],
                action=action,
                ip_address=ip_address,
                target_user_id=user.id,
                target_username=user.username,
                detail={"is_active": payload.enable}
            )

    status_text = "启用" if payload.enable else "禁用"
    return {
        "message": f"批量{status_text}完成，成功 {status_text} {updated_count} 个用户",
        "updated_count": updated_count,
        "failed_users": failed_users if failed_users else None
    }


@router.post("/users/batch-reset-password")
async def batch_reset_password(request: Request, payload: BatchResetPasswordRequest, current_admin: dict = Depends(require_admin)):
    """批量重置密码"""
    ip_address = get_client_ip(request)
    current_admin_id = int(current_admin["id"])

    updated_count = 0
    failed_users = []

    async with AsyncSessionLocal() as session:
        for user_id in payload.user_ids:
            user = await UserRepository.get_by_id(session, user_id)
            if not user:
                failed_users.append({"user_id": user_id, "reason": "用户不存在"})
                continue

            user.password_hash = hash_password(payload.password)
            await session.commit()

            updated_count += 1
            # 审计日志
            await create_audit_log(
                session=session,
                operator_id=current_admin_id,
                operator_username=current_admin["username"],
                action="RESET_PWD",
                ip_address=ip_address,
                target_user_id=user.id,
                target_username=user.username,
                detail={"batch": True}
            )

    return {
        "message": f"批量重置密码完成，成功重置 {updated_count} 个用户密码",
        "updated_count": updated_count,
        "failed_users": failed_users if failed_users else None
    }


# ===================== Export =====================

@router.get("/users/export")
async def export_users(
    request: Request,
    current_admin: dict = Depends(require_admin),
    search: Optional[str] = Query(None, description="搜索用户名"),
    role: Optional[str] = Query(None, pattern=r'^(admin|user)$', description="角色筛选"),
    activity_status: Optional[str] = Query(None, pattern=r'^(active_7d|active_30d|never_login)$', description="活动状态筛选")
):
    """导出用户列表为CSV"""
    async with AsyncSessionLocal() as session:
        query = select(UserModel)

        # 搜索条件
        if search:
            query = query.where(UserModel.username.like(f"%{search}%"))

        # 角色筛选
        if role:
            query = query.where(UserModel.role == role)

        # 活动状态筛选
        if activity_status:
            now = datetime.utcnow()
            if activity_status == "active_7d":
                threshold = now - timedelta(days=7)
                query = query.where(UserModel.last_login_at >= threshold)
            elif activity_status == "active_30d":
                threshold = now - timedelta(days=30)
                query = query.where(UserModel.last_login_at >= threshold)
            elif activity_status == "never_login":
                query = query.where(UserModel.last_login_at.is_(None))

        result = await session.execute(query)
        users_model = list(result.scalars().all())

        # 生成CSV
        async def generate_csv():
            yield "ID,用户名,角色,邮箱,全名,是否启用,最后登录时间,最后登录IP,登录尝试次数,创建时间\n"
            for user in users_model:
                yield (
                    f"{user.id},"
                    f"\"{user.username}\","
                    f"{user.role},"
                    f"\"{user.email or ''}\","
                    f"\"{user.full_name or ''}\","
                    f"{user.is_active},"
                    f"{user.last_login_at.isoformat() if user.last_login_at else ''},"
                    f"{user.last_login_ip or ''},"
                    f"{user.login_attempts},"
                    f"{user.created_at.isoformat() if user.created_at else ''}\n"
                )

        return StreamingResponse(
            generate_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=users_export.csv"}
        )


# ===================== User Statistics =====================

@router.get("/users/{user_id}/stats")
async def get_user_stats(user_id: int, current_admin: dict = Depends(require_admin)):
    """获取用户统计信息"""
    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 统计文档数量
        doc_count_result = await session.execute(
            select(func.count()).select_from(Document).where(Document.user_id == user_id)
        )
        document_count = doc_count_result.scalar() or 0

        # 统计会话数量
        session_count_result = await session.execute(
            select(func.count()).select_from(ChatSession).where(ChatSession.user_id == user_id)
        )
        session_count = session_count_result.scalar() or 0

        # 统计近7天会话数量
        now = datetime.utcnow()
        seven_days_ago = now - timedelta(days=7)
        recent_session_count_result = await session.execute(
            select(func.count()).select_from(ChatSession).where(
                and_(
                    ChatSession.user_id == user_id,
                    ChatSession.created_at >= seven_days_ago
                )
            )
        )
        recent_session_count = recent_session_count_result.scalar() or 0

        # 统计Token消耗量 (关联 ChatSession 和 ChatMessage)
        from app.models.chat import ChatMessage
        
        token_count_result = await session.execute(
            select(func.sum(ChatMessage.token_count)).where(
                and_(
                    ChatMessage.user_id == user_id,
                    ChatMessage.created_at >= seven_days_ago
                )
            )
        )
        recent_token_count = token_count_result.scalar() or 0
        

        return {
            "user_id": user_id,
            "username": user.username,
            "document_count": document_count,
            "session_count": session_count,
            "recent_session_count": recent_session_count,
            "recent_token_count": recent_token_count
        }


# ===================== Login History =====================

@router.get("/users/{user_id}/login-history")
async def get_login_history(
    user_id: int,
    current_admin: dict = Depends(require_admin),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量")
):
    """获取用户登录历史"""
    async with AsyncSessionLocal() as session:
        user = await UserRepository.get_by_id(session, user_id)
        if not user:
            raise HTTPException(status_code=404, detail="用户不存在")

        # 获取总数
        count_query = select(func.count(LoginHistory.id)).where(LoginHistory.user_id == user_id)
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # 分页查询
        offset = (page - 1) * size
        query = (
            select(LoginHistory)
            .where(LoginHistory.user_id == user_id)
            .order_by(LoginHistory.created_at.desc())
            .offset(offset)
            .limit(size)
        )

        result = await session.execute(query)
        records = list(result.scalars().all())

        login_history = []
        for record in records:
            login_history.append({
                "id": record.id,
                "user_id": record.user_id,
                "ip_address": record.ip_address,
                "user_agent": record.user_agent,
                "login_status": record.login_status,
                "fail_reason": record.fail_reason,
                "created_at": record.created_at.isoformat() if record.created_at else None
            })

        return {
            "data": login_history,
            "meta": {
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size if total > 0 else 0
            }
        }


# ===================== Audit Logs =====================

@router.get("/audit-logs")
async def list_audit_logs(
    request: Request,
    current_admin: dict = Depends(require_admin),
    page: int = Query(1, ge=1, description="页码"),
    size: int = Query(20, ge=1, le=100, description="每页数量"),
    operator_id: Optional[int] = Query(None, description="操作人ID筛选"),
    action: Optional[str] = Query(None, description="操作类型筛选"),
    start_date: Optional[str] = Query(None, description="开始日期 (ISO格式)"),
    end_date: Optional[str] = Query(None, description="结束日期 (ISO格式)")
):
    """获取审计日志列表（支持分页、筛选）"""
    async with AsyncSessionLocal() as session:
        query = select(AuditLog)
        count_query = select(func.count(AuditLog.id))

        # 操作人筛选
        if operator_id:
            query = query.where(AuditLog.operator_id == operator_id)
            count_query = count_query.where(AuditLog.operator_id == operator_id)

        # 操作类型筛选
        if action:
            query = query.where(AuditLog.action == action)
            count_query = count_query.where(AuditLog.action == action)

        # 日期范围筛选
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.where(AuditLog.created_at >= start_dt)
            count_query = count_query.where(AuditLog.created_at >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.where(AuditLog.created_at <= end_dt)
            count_query = count_query.where(AuditLog.created_at <= end_dt)

        # 获取总数
        total_result = await session.execute(count_query)
        total = total_result.scalar() or 0

        # 分页
        offset = (page - 1) * size
        query = query.order_by(AuditLog.created_at.desc()).offset(offset).limit(size)

        result = await session.execute(query)
        logs = list(result.scalars().all())

        audit_logs = []
        for log in logs:
            audit_logs.append({
                "id": log.id,
                "operator_id": log.operator_id,
                "operator_username": log.operator_username,
                "target_user_id": log.target_user_id,
                "target_username": log.target_username,
                "action": log.action,
                "detail": log.detail,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat() if log.created_at else None
            })

        return {
            "data": audit_logs,
            "meta": {
                "total": total,
                "page": page,
                "size": size,
                "pages": (total + size - 1) // size if total > 0 else 0
            }
        }


@router.get("/audit-logs/export")
async def export_audit_logs(
    request: Request,
    current_admin: dict = Depends(require_admin),
    operator_id: Optional[int] = Query(None, description="操作人ID筛选"),
    action: Optional[str] = Query(None, description="操作类型筛选"),
    start_date: Optional[str] = Query(None, description="开始日期 (ISO格式)"),
    end_date: Optional[str] = Query(None, description="结束日期 (ISO格式)")
):
    """导出审计日志为CSV"""
    async with AsyncSessionLocal() as session:
        query = select(AuditLog)

        # 操作人筛选
        if operator_id:
            query = query.where(AuditLog.operator_id == operator_id)

        # 操作类型筛选
        if action:
            query = query.where(AuditLog.action == action)

        # 日期范围筛选
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace("Z", "+00:00"))
            query = query.where(AuditLog.created_at >= start_dt)

        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace("Z", "+00:00"))
            query = query.where(AuditLog.created_at <= end_dt)

        query = query.order_by(AuditLog.created_at.desc())

        result = await session.execute(query)
        logs = list(result.scalars().all())

        # 生成CSV
        async def generate_csv():
            yield "ID,操作人ID,操作人用户名,目标用户ID,目标用户名,操作类型,详细信息,IP地址,操作时间\n"
            for log in logs:
                detail_str = str(log.detail) if log.detail else ""
                yield (
                    f"{log.id},"
                    f"{log.operator_id},"
                    f"\"{log.operator_username}\","
                    f"{log.target_user_id or ''},"
                    f"\"{log.target_username or ''}\","
                    f"{log.action},"
                    f"\"{detail_str}\","
                    f"{log.ip_address or ''},"
                    f"{log.created_at.isoformat() if log.created_at else ''}\n"
                )

        return StreamingResponse(
            generate_csv(),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=audit_logs_export.csv"}
        )
