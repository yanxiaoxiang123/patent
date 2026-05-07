# 用户管理系统完善方案

> 生成时间：2026-04-10
> 项目：智能专利辅助审核系统 (IPRS)

---

## 一、现状分析

### 1.1 已实现功能

| 模块 | 功能 | 状态 |
|------|------|------|
| 后端 API | 获取用户列表 `GET /admin/users` | ✅ |
| 后端 API | 创建用户 `POST /admin/users` | ✅ |
| 后端 API | 获取单个用户 `GET /admin/users/{user_id}` | ✅ |
| 后端 API | 更新用户 `PUT /admin/users/{user_id}` | ✅ |
| 后端 API | 删除用户 `DELETE /admin/users/{user_id}` | ✅ |
| 后端 API | 重置密码 `POST /admin/users/{user_id}/reset-password` | ✅ |
| 安全机制 | JWT Token 认证 (HS256, 24小时过期) | ✅ |
| 安全机制 | 密码哈希存储 (bcrypt) | ✅ |
| 前端 | 用户列表展示 | ✅ |
| 前端 | 新建用户对话框 | ✅ |
| 前端 | 删除用户（带确认） | ✅ |

### 1.2 缺失功能

| 优先级 | 缺失功能 | 说明 |
|--------|----------|------|
| **高** | 编辑用户功能 | 后端有 PUT API，前端无调用 |
| **高** | 用户状态管理 | 无法禁用/启用账户 |
| **高** | 登录失败锁定 | 无账户锁定机制 |
| **高** | 最后登录记录 | 缺少 last_login_at, last_login_ip |
| **中** | 用户搜索/筛选 | 无分页、搜索、角色筛选 |
| **中** | 密码强度校验 | 当前仅检查长度>=6 |
| **低** | 审计日志 | 无操作记录 |
| **低** | 用户个人中心 | 无法自行修改信息 |

---

## 二、实施方案

### 阶段一：基础完善（高优先级）

#### 2.1.1 后端模型增强

**文件**: `backend/app/models/user.py`

新增字段：

```python
from sqlalchemy import Column, Boolean, DateTime, String, Integer
from sqlalchemy.sql import func

class User(Base):
    # ... 现有字段 ...

    # 新增字段
    is_active = Column(Boolean, default=True, nullable=False)        # 用户状态
    last_login_at = Column(DateTime, nullable=True)                # 最后登录时间
    last_login_ip = Column(String(45), nullable=True)              # 最后登录IP
    login_attempts = Column(Integer, default=0, nullable=False)   # 登录失败次数
    locked_until = Column(DateTime, nullable=True)                 # 账户锁定截止时间
    email = Column(String(255), nullable=True)                    # 邮箱
    full_name = Column(String(100), nullable=True)                 # 全名
```

#### 2.1.2 登录安全增强

**文件**: `backend/app/api/auth.py`

修改登录逻辑：

```python
# 登录流程改进
1. 检查用户是否被锁定 (locked_until > 当前时间)
2. 验证密码
3. 登录成功：重置 login_attempts，记录 last_login_at, last_login_ip
4. 登录失败：login_attempts + 1，超过5次则设置 locked_until = now + 15分钟
```

新增 API：

```
PATCH /admin/users/{user_id}/toggle-status  # 切换用户状态
```

#### 2.1.3 前端类型和 API 完善

**文件**: `frontend/src/types/index.ts`

```typescript
export interface User {
  id: number;
  username: string;
  role: "user" | "admin" | "agent";
  email?: string;
  full_name?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  last_login_at?: string;
  last_login_ip?: string;
}
```

**文件**: `frontend/src/services/admin.ts`

新增函数：

```typescript
export const updateUser = async (userId: number, payload: Partial<User>): Promise<{message: string}> => {
  return await api.patch(`/admin/users/${userId}`, payload);
};

export const toggleUserStatus = async (userId: number): Promise<{message: string}> => {
  return await api.patch(`/admin/users/${userId}/toggle-status`);
};
```

#### 2.1.4 用户管理页面增强

**文件**: `frontend/src/views/AdminUsers.vue`

新增功能：
- 编辑用户对话框（修改角色、邮箱、姓名）
- 状态切换组件（启用/禁用）
- 搜索框（按用户名搜索）
- 角色筛选下拉框

---

### 阶段二：安全增强（中优先级）

#### 2.2.1 密码强度校验

**文件**: `backend/app/core/security.py`

新增密码校验函数：

```python
import re

def validate_password_strength(password: str) -> bool:
    """
    密码强度要求：
    - 至少8位
    - 包含大写字母
    - 包含小写字母
    - 包含数字
    """
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True
```

应用场景：
- 创建用户时
- 重置密码时
- 用户修改密码时

---

### 阶段三：审计日志（低优先级）

#### 2.3.1 审计日志表

**文件**: `backend/app/models/audit_log.py` (新建)

```python
class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(String(50), nullable=False)  # login, logout, create_user, update_user, delete_user
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)
    created_at = Column(DateTime, server_default=func.now())
```

---

## 三、API 变更汇总

### 3.1 新增端点

| 方法 | 路径 | 说明 |
|------|------|------|
| PATCH | `/admin/users/{user_id}/toggle-status` | 切换用户启用/禁用状态 |

### 3.2 修改端点

| 方法 | 路径 | 变更说明 |
|------|------|----------|
| POST | `/auth/login` | 增加登录失败锁定逻辑 |
| GET | `/admin/users` | 增加分页、搜索、筛选参数 |

### 3.3 查询参数

```
GET /admin/users?page=1&size=20&search=username&role=admin
```

| 参数 | 类型 | 说明 |
|------|------|------|
| page | int | 页码，默认1 |
| size | int | 每页数量，默认20 |
| search | string | 用户名搜索关键字 |
| role | string | 角色筛选 |

---

## 四、数据库变更

```sql
-- 新增字段到 users 表
ALTER TABLE users
ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL,
ADD COLUMN last_login_at DATETIME NULL,
ADD COLUMN last_login_ip VARCHAR(45) NULL,
ADD COLUMN login_attempts INT DEFAULT 0 NOT NULL,
ADD COLUMN locked_until DATETIME NULL,
ADD COLUMN email VARCHAR(255) NULL,
ADD COLUMN full_name VARCHAR(100) NULL;

-- 新建审计日志表
CREATE TABLE audit_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    action VARCHAR(50) NOT NULL,
    details JSON NULL,
    ip_address VARCHAR(45) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

---

## 五、文件变更清单

### 后端

| 文件 | 操作 | 说明 |
|------|------|------|
| `backend/app/models/user.py` | 修改 | 新增字段 |
| `backend/app/models/__init__.py` | 修改 | 导出 AuditLog 模型 |
| `backend/app/api/auth.py` | 修改 | 登录安全增强 |
| `backend/app/api/admin.py` | 修改 | 新增 toggle-status API，分页支持 |
| `backend/app/core/security.py` | 修改 | 新增密码强度校验 |

### 前端

| 文件 | 操作 | 说明 |
|------|------|------|
| `frontend/src/types/index.ts` | 修改 | 补充 User 类型 |
| `frontend/src/services/admin.ts` | 修改 | 新增 updateUser, toggleUserStatus |
| `frontend/src/views/AdminUsers.vue` | 修改 | 编辑功能、状态切换、搜索筛选 |

### 新建文件

| 文件 | 说明 |
|------|------|
| `backend/app/models/audit_log.py` | 审计日志模型 |

---

## 六、风险评估

| 风险 | 级别 | 缓解措施 |
|------|------|----------|
| 数据库字段变更 | 中 | 提供 SQL 迁移脚本，测试环境先行 |
| 登录逻辑修改 | 中 | 保留原有逻辑作为 fallback |
| 前端状态管理 | 低 | 使用 Pinia 状态管理 |

---

## 七、预估工时

| 阶段 | 后端 | 前端 | 测试 | 合计 |
|------|------|------|------|------|
| 阶段一 | 3h | 2h | 1h | 6h |
| 阶段二 | 1h | 0.5h | 0.5h | 2h |
| 阶段三 | 2h | 0h | 0.5h | 2.5h |
| **总计** | 6h | 2.5h | 2h | **10.5h** |

---

## 八、测试用例

### 8.1 登录安全测试

| 用例 | 预期结果 |
|------|----------|
| 连续5次密码错误 | 第6次登录被锁定15分钟 |
| 锁定期间登录 | 返回"账户已锁定"错误 |
| 锁定超时后登录 | 正常登录，login_attempts 重置 |
| 正确密码登录 | 记录 last_login_at 和 last_login_ip |

### 8.2 用户管理测试

| 用例 | 预期结果 |
|------|----------|
| 管理员禁用用户 | 用户无法登录 |
| 管理员启用用户 | 用户恢复登录 |
| 编辑用户信息 | 信息正确更新 |
| 搜索用户名 | 返回匹配用户列表 |
| 角色筛选 | 返回指定角色用户 |

### 8.3 密码强度测试

| 用例 | 预期结果 |
|------|----------|
| 密码"123456" | 拒绝（无大小写字母） |
| 密码"abcdefgh" | 拒绝（无数字） |
| 密码"Ab123456" | 拒绝（少于8位） |
| 密码"Abcdefgh1" | 接受 |
