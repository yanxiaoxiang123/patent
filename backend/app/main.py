from fastapi import FastAPI, Request
from fastapi import Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import os
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 创建 FastAPI 应用
app = FastAPI(
    title="智能专利辅助审核系统 (IPRS)",
    description="基于 AI 的专利文档智能审核平台",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS 配置
origins = os.getenv(
    "CORS_ORIGINS",
    '["http://localhost:3000", "http://localhost:8080", "http://localhost:3005", "http://127.0.0.1:3000", "http://127.0.0.1:8080", "http://127.0.0.1:3005"]',
)
if isinstance(origins, str):
    import json
    try:
        origins = json.loads(origins)
    except:
        origins = origins.strip("[]").replace(" ", "").replace('"', "").split(",")


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    return JSONResponse(
        status_code=500,
        content={"message": "服务器内部错误", "detail": str(exc)}
    )

# 健康检查端点
@app.get("/")
async def root():
    return {"message": "智能专利辅助审核系统 API", "status": "running"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "IPRS API"}

# 注册路由
from app.api import documents, chat
app.include_router(documents.router, prefix="/api/documents", tags=["文档管理"])
app.include_router(chat.router, prefix="/api/ai", tags=["专利AI对话"])

# 直接在 main.py 中定义认证与管理员路由
from pydantic import BaseModel
import aiomysql
import hashlib
from typing import Optional, List, Dict

class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

def verify_password(plain_password: str, stored_password: str) -> bool:
    """验证密码 - 支持 SHA256 哈希和明文密码"""
    if not stored_password:
        return False
    stored = stored_password.strip()
    hashed_plain = hashlib.sha256(plain_password.encode()).hexdigest()
    if hashed_plain.lower() == stored.lower():
        return True
    return plain_password == stored

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123123',
    'db': 'iprs',
    'autocommit': True
}

async def get_user_from_db(username: str):
    """从数据库获取用户"""
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        cursor = await conn.cursor()
        await cursor.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = %s",
            (username,)
        )
        result = await cursor.fetchone()
        await cursor.close()
        conn.close()
        return result
    except Exception as e:
        print(f"数据库查询错误: {e}")
        return None

def parse_simple_token(auth_header: Optional[str]) -> Optional[Dict[str, str]]:
    """
    解析简单令牌格式 simple_token_{id}_{username}
    返回 {'id': str, 'username': str} 或 None
    """
    if not auth_header:
        return None
    if auth_header.lower().startswith("bearer "):
        token = auth_header[7:].strip()
    else:
        token = auth_header.strip()
    parts = token.split("_")
    if len(parts) >= 4 and parts[0] == "simple" and parts[1] == "token":
        return {"id": parts[2], "username": "_".join(parts[3:])}
    return None

async def get_current_user_simple(request: Request) -> Dict[str, str]:
    """从 Authorization 头解析当前用户并校验存在"""
    auth = request.headers.get("Authorization")
    info = parse_simple_token(auth)
    if not info or not info.get("username"):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未认证")
    db_user = await get_user_from_db(info["username"])
    if not db_user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户不存在")
    user_id, username, password_hash, role = db_user
    return {"id": str(user_id), "username": username, "role": role or "user"}

async def require_admin(request: Request) -> Dict[str, str]:
    """管理员权限校验"""
    user = await get_current_user_simple(request)
    if user.get("role") != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="需要管理员权限")
    return user

@app.post("/api/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    """用户登录"""
    try:
        print(f"尝试登录用户: {user_data.username}")

        conn = await aiomysql.connect(**DB_CONFIG)
        cursor = await conn.cursor()

        await cursor.execute(
            "SELECT id, username, password_hash, role FROM users WHERE username = %s",
            (user_data.username,)
        )
        result = await cursor.fetchone()

        await cursor.close()
        conn.close()

        if not result:
            print(f"用户不存在: {user_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名不存在"
            )

        user_id, username, password_hash, role = result

        if not verify_password(user_data.password, password_hash):
            print(f"密码错误: {user_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="密码错误"
            )

        print(f"登录成功: {user_data.username}")

        access_token = f"simple_token_{user_id}_{username}"

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user_id,
                "username": username,
                "email": None,
                "full_name": None,
                "role": role
            }
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"登录过程中发生错误: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"登录过程中发生错误: {str(e)}"
        )

@app.get("/api/auth/me")
async def get_current_user_info():
    """获取当前用户信息"""
    return {"message": "认证API工作正常"}

@app.post("/api/auth/logout")
async def logout():
    """用户登出"""
    return {"message": "登出成功"}

# ===================== 管理员用户管理接口 =====================

class CreateUserRequest(BaseModel):
    username: str
    password: str
    email: Optional[str] = None
    full_name: Optional[str] = None

class UserItem(BaseModel):
    id: int
    username: str
    role: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    created_at: Optional[str] = None

@app.get("/api/admin/users")
async def list_users(current_admin: dict = Depends(require_admin)):
    """管理员获取用户列表"""
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        cursor = await conn.cursor()
        await cursor.execute("SELECT id, username, role, created_at FROM users ORDER BY id ASC")
        rows = await cursor.fetchall()
        await cursor.close()
        conn.close()
        users: List[Dict[str, str]] = []
        for r in rows:
            users.append({
                "id": r[0],
                "username": r[1],
                "role": r[2],
                "created_at": r[3].isoformat() if r[3] else None
            })
        return {"data": users}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取用户列表失败: {e}")

@app.post("/api/admin/users")
async def create_user_admin(payload: CreateUserRequest, current_admin: dict = Depends(require_admin)):
    """管理员创建普通用户（role 固定为 user）"""
    try:
        # 计算 SHA256 哈希以兼容现有密码校验
        hashed = hashlib.sha256(payload.password.encode()).hexdigest()
        conn = await aiomysql.connect(**DB_CONFIG)
        cursor = await conn.cursor()
        # 检查是否已存在
        await cursor.execute("SELECT id FROM users WHERE username = %s", (payload.username,))
        exists = await cursor.fetchone()
        if exists:
            await cursor.close()
            conn.close()
            raise HTTPException(status_code=400, detail="用户名已存在")
        # 插入用户
        await cursor.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s)",
            (payload.username, hashed, "user")
        )
        await conn.commit()
        await cursor.close()
        conn.close()
        return {"message": "创建成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建用户失败: {e}")

@app.delete("/api/admin/users/{user_id}")
async def delete_user_admin(user_id: int, current_admin: dict = Depends(require_admin)):
    """管理员删除用户"""
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        cursor = await conn.cursor()
        await cursor.execute("DELETE FROM users WHERE id = %s", (user_id,))
        await conn.commit()
        affected = cursor.rowcount
        await cursor.close()
        conn.close()
        if affected == 0:
            raise HTTPException(status_code=404, detail="用户不存在")
        return {"message": "删除成功"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除用户失败: {e}")

# 其他路由 (稍后添加)
# from app.api import review
# app.include_router(review.router, prefix="/api/review", tags=["审核"])

if __name__ == "__main__":
    debug = os.getenv("DEBUG", "False").lower() == "true"
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=debug,
        log_level="info",
        access_log=True,
        use_colors=False
    )
