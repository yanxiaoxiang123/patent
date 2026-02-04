-- 创建数据库
CREATE DATABASE IF NOT EXISTS iprs CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- 使用数据库
USE iprs;

-- 用户表
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
    role VARCHAR(20) DEFAULT 'agent' COMMENT '角色: agent/admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表';

-- 专利文档表
CREATE TABLE documents (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '用户ID',
    title VARCHAR(255) COMMENT '文档标题',
    file_path VARCHAR(512) NOT NULL COMMENT '文件存储路径',
    file_type VARCHAR(10) COMMENT '文件类型: pdf/docx',
    file_size BIGINT COMMENT '文件大小(字节)',
    parsed_content JSON COMMENT '解析后的结构化内容',
    status VARCHAR(20) DEFAULT 'uploaded' COMMENT '状态: uploaded/parsing/reviewed/completed',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_status (user_id, status),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='专利文档表';

-- 审核记录表
CREATE TABLE review_records (
    id INT AUTO_INCREMENT PRIMARY KEY,
    document_id INT NOT NULL COMMENT '文档ID',
    review_type VARCHAR(50) COMMENT '审核类型: formal_check/logic_check',
    model_version VARCHAR(50) COMMENT '模型版本: qwen3-7b/coze-bot-v1',
    result_json JSON COMMENT 'AI审核结果JSON',
    score INT COMMENT '质量评分(0-100)',
    error_count INT DEFAULT 0 COMMENT '错误数量',
    processing_time DECIMAL(10,3) COMMENT '处理耗时(秒)',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE,
    INDEX idx_document_type (document_id, review_type),
    INDEX idx_created_at (created_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审核记录表';