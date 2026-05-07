-- 用户管理功能增强 - 数据库迁移脚本
-- 执行时间: 2026-04-10
-- 注意事项: 请先备份数据库后再执行

-- 1. 添加 is_active 字段（默认启用）
ALTER TABLE users
ADD COLUMN is_active BOOLEAN DEFAULT TRUE NOT NULL AFTER role;

-- 2. 添加登录相关字段
ALTER TABLE users
ADD COLUMN last_login_at DATETIME NULL AFTER is_active,
ADD COLUMN last_login_ip VARCHAR(45) NULL AFTER last_login_at,
ADD COLUMN login_attempts INT DEFAULT 0 NOT NULL AFTER last_login_ip,
ADD COLUMN locked_until DATETIME NULL AFTER login_attempts;

-- 3. 扩展 email 字段长度（原为100，现为255以支持更长邮箱）
ALTER TABLE users
MODIFY COLUMN email VARCHAR(255) NULL COMMENT '邮箱';

-- 4. 添加索引以提高查询性能
CREATE INDEX idx_users_username ON users(username);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_role ON users(role);

-- 验证执行结果
DESCRIBE users;
