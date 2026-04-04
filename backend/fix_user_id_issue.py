import re

# 读取文件
with open('app/api/v1/query_history.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 current_user.id 为 int(current_user.username) 因为 username 就是用户 ID 字符串
# 但更好的方式是直接从数据库获取 user_id
# 这里我们简单地将 username 转换为整数（假设 username 是数字字符串）
# 实际上应该使用 current_user.username 并查询对应的 user_id

# 替换：current_user.id -> (SELECT user_id FROM sys_users WHERE username = current_user.username LIMIT 1)
# 但这太复杂了，让我们直接在 SQL 中使用 username

# 最简单的方案：假设 admin 的 user_id 是 1
# 实际上应该在函数中查询

print("需要手动修复：current_user.id 应该替换为从数据库查询的 user_id")
print("或者修改 JWT token 中包含 user_id")
