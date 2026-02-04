"""
简化的用户认证API
"""
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from typing import Optional, Dict, Any
import aiomysql
import os
from dotenv import load_dotenv

load_dotenv()

# 路由器
router = APIRouter()

# 数据库配置
DB_CONFIG = {
    'host': 'localhost',
    'port': 3306,
    'user': 'root',
    'password': '123123',
    'db': 'iprs',
    'autocommit': True
}

# Pydantic 模型
class UserLogin(BaseModel):
    username: str
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user: dict

async def get_user_from_db(username: str) -> Optional[Dict[str, Any]]:
    """从数据库获取用户"""
    try:
        conn = await aiomysql.connect(**DB_CONFIG)
        cursor = await conn.cursor()

        await cursor.execute(
            "SELECT id, username, password_hash, role, email, full_name FROM users WHERE username = %s",
            (username,)
        )
        result = await cursor.fetchone()

        await cursor.close()
        conn.close()

        if result:
            return {
                'id': result[0],
                'username': result[1],
                'password_hash': result[2],
                'role': result[3],
                'email': result[4],
                'full_name': result[5]
            }
        return None
    except Exception as e:
        print(f"数据库查询错误: {e}")
        return None

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """用户登录"""
    try:
        print(f"尝试登录用户: {user_data.username}")

        # 获取用户
        user = await get_user_from_db(user_data.username)
        if not user:
            print(f"用户不存在: {user_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="用户名不存在"
            )

        # 验证密码 - 临时使用明文比较
        if user_data.password != user['password_hash']:
            print(f"密码错误: {user_data.username}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="密码错误"
            )

        print(f"登录成功: {user_data.username}")

        # 简单的访问令牌（生产环境应使用JWT）
        access_token = f"simple_token_{user['id']}_{user['username']}"

        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "id": user['id'],
                "username": user['username'],
                "email": user['email'],
                "full_name": user['full_name'],
                "role": user['role']
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

@router.get("/me")
async def get_current_user_info():
    """获取当前用户信息（简化版）"""
    return {"message": "认证API工作正常"}

@router.post("/logout")
async def logout():
    """用户登出"""
    return {"message": "登出成功"}