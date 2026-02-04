-- 使用数据库
USE iprs;

-- 插入一个测试管理员用户（密码：admin123 的哈希值）
INSERT INTO users (username, password_hash, role) VALUES
('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewdBPj3bp.Gm.F5e', 'admin');

-- 插入一个测试普通用户（密码：123456 的哈希值）
INSERT INTO users (username, password_hash, role) VALUES
('lizhuanyuan', '$2b$12$EixZaYVK1fsbw1ZfbX3OXePaWxn96p36WQoeG6Lruj3vjPGga31lW', 'agent');

-- 验证数据插入
SELECT * FROM users;