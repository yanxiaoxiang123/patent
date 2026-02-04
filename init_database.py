import pymysql
import hashlib
import sys

def create_database():
    try:
        # 先连接到 MySQL 服务器（不指定数据库）
        connection = pymysql.connect(
            host='localhost',
            user='root',
            password='123123',
            charset='utf8mb4'
        )

        print("✅ 成功连接到 MySQL 服务器")

        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute("CREATE DATABASE IF NOT EXISTS iprs CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ 数据库 'iprs' 创建成功")

            # 使用数据库
            cursor.execute("USE iprs")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL COMMENT '用户名',
                    password_hash VARCHAR(255) NOT NULL COMMENT '密码哈希',
                    email VARCHAR(100) NULL COMMENT '邮箱',
                    full_name VARCHAR(100) NULL COMMENT '全名',
                    role VARCHAR(20) DEFAULT 'agent' COMMENT '角色: agent/admin',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间'
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='用户表'
            """)
            print("✅ 用户表创建成功")

            # 创建文档表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS documents (
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
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='专利文档表'
            """)
            print("✅ 文档表创建成功")

            # 创建审核记录表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS review_records (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    document_id INT NOT NULL COMMENT '文档ID',
                    review_type VARCHAR(50) COMMENT '审核类型: formal_check/logic_check',
                    model_version VARCHAR(50) COMMENT '模型版本: qwen3-7b/coze-bot-v1',
                    result_json JSON COMMENT 'AI审核结果JSON',
                    score INT COMMENT '质量评分(0-100)',
                    error_count INT DEFAULT 0 COMMENT '错误数量',
                    processing_time DECIMAL(10,3) COMMENT '处理耗时(秒)',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE CASCADE
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='审核记录表'
            """)
            print("✅ 审核记录表创建成功")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT NOT NULL,
                    title VARCHAR(255),
                    model VARCHAR(50),
                    document_id INT NULL,
                    last_message_at TIMESTAMP NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天会话表'
            """)
            print("✅ 聊天会话表创建成功")

            cursor.execute("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    session_id INT NOT NULL,
                    user_id INT NULL,
                    role VARCHAR(20) NOT NULL,
                    content LONGTEXT NOT NULL,
                    model VARCHAR(50),
                    token_count INT,
                    document_id INT NULL,
                    metadata JSON,
                    message_index INT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL,
                    FOREIGN KEY (document_id) REFERENCES documents(id) ON DELETE SET NULL
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='聊天消息表'
            """)
            print("✅ 聊天消息表创建成功")

            # 插入测试数据
            # 简单密码哈希（生产环境应使用 bcrypt）
            admin_password_hash = hashlib.sha256("admin123".encode()).hexdigest()
            user_password_hash = hashlib.sha256("123456".encode()).hexdigest()

            cursor.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
            admin_exists = cursor.fetchone()[0]

            if admin_exists == 0:
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role) VALUES
                    (%s, %s, 'admin'),
                    ('lizhuanyuan', %s, 'agent')
                """, ('admin', admin_password_hash, user_password_hash))
                print("✅ 测试用户创建成功")
            else:
                print("⚠️  测试用户已存在，跳过插入")

        connection.commit()
        print("\n🎉 数据库初始化完成！")

        # 验证数据
        with connection.cursor() as cursor:
            cursor.execute("USE iprs")
            cursor.execute("SELECT username, role FROM users")
            users = cursor.fetchall()
            print("\n📋 当前用户列表：")
            for user in users:
                print(f"  - {user[0]} ({user[1]})")

    except pymysql.Error as e:
        print(f"❌ 数据库错误: {e}")
        print("\n请检查：")
        print("1. MySQL 服务是否启动")
        print("2. 用户名密码是否正确 (root/123456)")
        print("3. MySQL 是否允许远程连接")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 其他错误: {e}")
        sys.exit(1)
    finally:
        if 'connection' in locals():
            connection.close()

if __name__ == "__main__":
    create_database()
