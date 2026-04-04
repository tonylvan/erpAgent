"""
修复 query_history.py 中的 UserInfo 和 user_id 问题
"""
import re

# 读取文件
with open('app/api/v1/query_history.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. 添加 UserInfo 导入
content = re.sub(
    r'from app\.api\.v1\.auth import get_current_user$',
    'from app.api.v1.auth import get_current_user, UserInfo',
    content,
    flags=re.MULTILINE
)

# 2. 添加辅助函数（在 logger 之后）
helper_func = '''
def get_user_id_from_username(db, username: str) -> int:
    """根据用户名获取用户 ID"""
    cursor = db.cursor()
    cursor.execute("SELECT user_id FROM sys_users WHERE username = %s LIMIT 1", (username,))
    row = cursor.fetchone()
    cursor.close()
    if row:
        return row[0]
    raise HTTPException(status_code=404, detail="用户不存在")

'''
content = re.sub(
    r'(logger = logging\.getLogger\(__name__\))',
    r'\1' + helper_func,
    content
)

# 3. 修改函数签名：current_user: dict -> current_user: UserInfo
content = re.sub(
    r'current_user: dict = Depends\(get_current_user\)',
    'current_user: UserInfo = Depends(get_current_user)',
    content
)

# 4. 替换 current_user["user_id"] 为 get_user_id_from_username(db, current_user.username)
content = re.sub(
    r'current_user\["user_id"\]',
    'get_user_id_from_username(db, current_user.username)',
    content
)

# 写回文件
with open('app/api/v1/query_history.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] 修复完成！")
print("  1. 添加 UserInfo 导入")
print("  2. 添加 get_user_id_from_username 辅助函数")
print("  3. 修改 current_user 类型为 UserInfo")
print("  4. 替换所有 current_user['user_id'] 为 get_user_id_from_username(db, current_user.username)")
