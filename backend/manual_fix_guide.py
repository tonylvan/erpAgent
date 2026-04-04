import re

# 读取文件
with open('app/api/v1/query_history.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 替换 current_user.id 为直接使用 current_user.username
# 因为 JWT 中只有 username，我们需要在 SQL 中查询对应的 user_id
# 或者简单地，我们假设用户名就是用户标识符，直接使用字符串

# 方案 1：修改 SQL，使用 username 查询
# 方案 2：在函数开始时查询 user_id

# 这里使用方案 1，直接在 SQL 中使用子查询获取 user_id

# 替换所有 current_user.id 为适当的处理
# 对于 INSERT/UPDATE，我们需要实际的整数 user_id
# 让我们添加一个查询来获取 user_id

print("Fixing user_id issue...")

# 在 save_query_history 函数中添加获取 user_id 的逻辑
# 这需要手动编辑，因为每个函数不同

print("需要手动修复每个函数")
