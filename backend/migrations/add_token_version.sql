-- 添加 token_version 列到 users 表
-- 用于 Token 批量失效机制：管理员可递增此值强制下线用户
-- 执行前请备份数据库

ALTER TABLE users
ADD COLUMN token_version INT NOT NULL DEFAULT 0
COMMENT 'Token版本号，递增可批量失效旧Token'
AFTER locked_until;
