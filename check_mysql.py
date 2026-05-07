import pymysql
import subprocess
import sys
import os

def check_mysql_service():
    print("🔍 检查 MySQL 服务状态...")
    try:
        # 在 Windows 上检查 MySQL 服务
        result = subprocess.run(['sc', 'query', 'mysql80'], capture_output=True, text=True)
        if 'RUNNING' in result.stdout:
            print("✅ MySQL80 服务正在运行")
        else:
            print("❌ MySQL80 服务未运行")
            print("请启动 MySQL 服务或使用命令: net start mysql80")
            return False
    except Exception as e:
        print(f"⚠️  无法检查服务状态: {e}")

    return True

import os

def test_connection(username='root', password='', host='localhost', port=3306):
    print(f"\n🔗 尝试连接 MySQL: {username}@{host}:{port}")
    try:
        connection = pymysql.connect(
            host=host,
            user=username,
            password=password,
            port=port,
            charset='utf8mb4'
        )
        print("✅ 连接成功！")
        return True, connection
    except pymysql.Error as e:
        print(f"❌ 连接失败: {e}")
        return False, None

def main():
    # 检查服务状态
    if not check_mysql_service():
        return

    db_password = os.getenv("DB_PASSWORD")
    if not db_password:
        print("❌ 请设置环境变量 DB_PASSWORD")
        return

    success, conn = test_connection('root', db_password)
    if success:
        print(f"\n✅ 数据库连接成功")
        if conn:
            conn.close()
    else:
        print("\n❌ 数据库连接失败，请检查密码是否正确")

if __name__ == "__main__":
    main()