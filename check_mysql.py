import pymysql
import subprocess
import sys

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

    # 常见的密码组合尝试
    common_configs = [
        ('root', '123456'),
        ('root', ''),
        ('root', 'root'),
        ('root', 'mysql'),
        ('root', 'password'),
        ('root', '12345'),
    ]

    print("\n🔐 尝试常见密码组合...")
    success = False

    for username, password in common_configs:
        success, conn = test_connection(username, password)
        if success:
            print(f"\n✅ 找到正确配置: {username}/{password}")
            if conn:
                conn.close()
            print(f"\n请使用以下配置更新 init_database.py:")
            print(f"用户名: {username}")
            print(f"密码: {password}")
            break

    if not success:
        print("\n❌ 无法找到正确的用户名密码组合")
        print("\n请手动检查:")
        print("1. MySQL 安装时设置的具体密码")
        print("2. 是否创建了其他用户")
        print("3. 是否需要重置 root 密码")

        print("\n📝 重置 root 密码的方法:")
        print("1. 停止 MySQL 服务")
        print("2. 以跳过权限验证模式启动 MySQL")
        print("3. 连接并重置密码")
        print("4. 正常重启 MySQL 服务")

if __name__ == "__main__":
    main()