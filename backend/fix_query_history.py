import re

# 读取文件
with open('app/api/v1/query_history.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 1: 导入 UserInfo
content = re.sub(
    r'from app\.api\.v1\.auth import get_current_user$',
    'from app.api.v1.auth import get_current_user, UserInfo',
    content,
    flags=re.MULTILINE
)

# 替换 2: 函数签名中的 current_user 类型
content = re.sub(
    r'current_user: dict = Depends\(get_current_user\)',
    'current_user: UserInfo = Depends(get_current_user)',
    content
)

# 替换 3: current_user["user_id"] -> current_user.id
content = re.sub(
    r'current_user\["user_id"\]',
    'current_user.id',
    content
)

# 写回文件
with open('app/api/v1/query_history.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Fixed query_history.py")
print(f"  - Added UserInfo import")
print(f"  - Changed current_user type to UserInfo")
print(f"  - Changed current_user['user_id'] to current_user.id")
