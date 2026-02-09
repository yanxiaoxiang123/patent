"""密码哈希工具"""
import hashlib
from passlib.context import CryptContext


_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """哈希密码"""
    return _pwd_context.hash(password)


def verify_password(plain_password: str, stored_password: str) -> bool:
    """验证密码 - 兼容 SHA256 与 bcrypt"""
    if not stored_password:
        return False

    stored = stored_password.strip()
    if stored.startswith("$2"):
        return _pwd_context.verify(plain_password, stored)

    hashed_plain = hashlib.sha256(plain_password.encode()).hexdigest()
    return hashed_plain.lower() == stored.lower()


def needs_rehash(stored_password: str) -> bool:
    """判断是否需要升级哈希"""
    if not stored_password:
        return False

    stored = stored_password.strip()
    if stored.startswith("$2"):
        return _pwd_context.needs_update(stored)

    return True
