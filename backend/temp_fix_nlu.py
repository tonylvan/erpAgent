# 临时禁用 NLU 模块，让后端先启动起来
# 修改 smart_query_v3.py，注释掉 NLU 相关导入

import sys

# 读取文件
with open(r"D:\erpAgent\backend\app\api\v1\smart_query_v3.py", "r", encoding="utf-8") as f:
    content = f.read()

# 注释掉 NLU 相关行
lines = content.split('\n')
new_lines = []
for line in lines:
    if 'from app.nlu.intent_parser import' in line or 'nlu_engine = NLUEngine()' in line:
        new_lines.append('# ' + line)  # 注释掉
    else:
        new_lines.append(line)

# 写回文件
with open(r"D:\erpAgent\backend\app\api\v1\smart_query_v3.py", "w", encoding="utf-8") as f:
    f.write('\n'.join(new_lines))

print("✅ 已临时禁用 NLU 模块")
