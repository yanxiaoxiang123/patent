import pymysql
import subprocess
import sys
import socket

def check_mysql_port():
    """检查 MySQL 端口是否开放"""
    print("🔍 检查 MySQL 端口...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('localhost', 3306))
        sock.close()

        if result == 0:
            print("✅ 端口 3306 可访问")
            return True
        else:
            print("❌ 端口 3306 不可访问")
            return False
    except Exception as e:
        print(f"❌ 端口检查错误: {e}")
        return False

def check_mysql_service_details():
    """检查 MySQL 服务详细状态"""
    print("\n🔍 检查 MySQL 服务详细信息...")
    try:
        # 检查 MySQL 服务状态
        result = subprocess.run(['sc', 'query', 'mysql80'], capture_output=True, text=True)
        print("MySQL80 服务状态:")
        print(result.stdout)

        # 尝试获取 MySQL 版本信息
        try:
            mysql_path = r"C:\Program Files\MySQL\MySQL Server 8.0\bin\mysql.exe"
            result = subprocess.run([mysql_path, '--version'], capture_output=True, text=True, timeout=5)
            print(f"MySQL 版本: {result.stdout.strip()}")
        except Exception as e:
            print(f"无法获取 MySQL 版本: {e}")

    except Exception as e:
        print(f"❌ 检查服务状态失败: {e}")

def test_different_connections():
    """测试不同的连接配置"""
    print("\n🔗 测试不同连接配置...")

    configs = [
        {'host': 'localhost', 'port': 3306},
        {'host': '127.0.0.1', 'port': 3306},
        {'host': 'localhost', 'port': 3307},  # 可能的备用端口
        {'host': '127.0.0.1', 'port': 3307},
    ]

    for config in configs:
        print(f"\n测试连接: {config['host']}:{config['port']}")
        try:
            connection = pymysql.connect(
                host=config['host'],
                user='root',
                password='123456',
                port=config['port'],
                charset='utf8mb4',
                connect_timeout=3
            )
            print(f"✅ 连接成功！配置: {config}")

            # 测试数据库操作
            with connection.cursor() as cursor:
                cursor.execute("SHOW DATABASES;")
                databases = cursor.fetchall()
                print(f"可用数据库: {[db[0] for db in databases]}")

            connection.close()
            return config

        except pymysql.Error as e:
            print(f"❌ 连接失败: {e}")

    return None

def create_database_with_config(config):
    """使用成功的配置创建数据库"""
    print(f"\n🏗️  使用配置创建数据库: {config}")

    try:
        connection = pymysql.connect(
            host=config['host'],
            port=config['port'],
            user='root',
            password='123456',
            charset='utf8mb4'
        )

        with connection.cursor() as cursor:
            # 创建数据库
            cursor.execute("CREATE DATABASE IF NOT EXISTS iprs CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print("✅ 数据库 'iprs' 创建成功")

            # 创建用户表
            cursor.execute("USE iprs")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(50) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    role VARCHAR(20) DEFAULT 'agent',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
            """)
            print("✅ 用户表创建成功")

            # 插入测试用户（使用简单哈希）
            import hashlib
            admin_hash = hashlib.sha256("admin123".encode()).hexdigest()
            user_hash = hashlib.sha256("123456".encode()).hexdigest()

            cursor.execute("SELECT COUNT(*) FROM users WHERE username='admin'")
            if cursor.fetchone()[0] == 0:
                cursor.execute("""
                    INSERT INTO users (username, password_hash, role) VALUES
                    ('admin', %s, 'admin'),
                    ('lizhuanyuan', %s, 'agent')
                """, (admin_hash, user_hash))
                print("✅ 测试用户创建成功")

        connection.commit()
        print("\n🎉 数据库初始化完成！")
        return True

    except Exception as e:
        print(f"❌ 创建数据库失败: {e}")
        return False
    finally:
        if 'connection' in locals():
            connection.close()

def main():
    print("=== MySQL 高级诊断工具 ===\n")

    # 检查端口
    if not check_mysql_port():
        print("\n❌ MySQL 端口不可访问，请检查 MySQL 服务是否正常启动")
        return

    # 检查服务详情
    check_mysql_service_details()

    # 测试不同连接配置
    working_config = test_different_connections()

    if working_config:
        print(f"\n✅ 找到可用配置: {working_config}")

        # 创建数据库
        if create_database_with_config(working_config):
            print(f"\n✅ 数据库创建成功！")
            print(f"请保存配置信息: {working_config}")

            # 创建配置文件
            with open('database_config.txt', 'w') as f:
                f.write(f"DATABASE_CONFIG = {working_config}\n")
                f.write("USERNAME = root\n")
                f.write("PASSWORD = 123456\n")
            print("📝 配置已保存到 database_config.txt")
        else:
            print("\n❌ 数据库创建失败")
    else:
        print("\n❌ 无法找到可用的数据库连接配置")
        print("\n建议:")
        print("1. 检查 MySQL 服务是否正常启动")
        print("2. 确认 root 用户密码")
        print("3. 检查防火墙设置")
        print("4. 尝试重置 MySQL root 密码")

if __name__ == "__main__":
    main()