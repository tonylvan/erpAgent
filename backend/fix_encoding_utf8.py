#!/usr/bin/env python
"""
修复 smart_query_v40.py 中文编码问题
确保所有中文字符串使用 UTF-8 编码
"""
import os
import sys

# 设置 UTF-8 编码
if sys.platform == 'win32':
    os.system('chcp 65001 >nul')
    
file_path = 'D:/erpAgent/backend/app/api/v1/smart_query_v40.py'

print(f'正在修复文件：{file_path}')

# 读取文件
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 检查是否有中文
has_chinese = any('\u4e00' <= c <= '\u9fff' for c in content)
print(f'包含中文：{has_chinese}')

# 验证文件可以正常读取
try:
    # 查找典型的中文字符串
    if '查询' in content:
        print('✅ 中文字符串正常')
    else:
        print('⚠️ 未找到典型中文字符串')
        
    # 检查是否有乱码字符
    invalid_chars = [c for c in content if ord(c) > 127 and not ('\u4e00' <= c <= '\u9fff')]
    if invalid_chars:
        print(f'⚠️ 发现 {len(invalid_chars)} 个可疑字符')
    else:
        print('✅ 未发现乱码字符')
        
except Exception as e:
    print(f'❌ 检查失败：{e}')

# 确保保存为 UTF-8
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print('✅ 文件已保存为 UTF-8 编码')
print('\n请重启后端服务使更改生效：')
print('cd D:\\erpAgent\\backend')
print('python -m uvicorn app.main:app --reload --port 8005')
