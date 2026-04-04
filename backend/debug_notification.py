"""
检查通知弹窗问题的调试脚本
"""
import requests
import re

# 获取前端页面
response = requests.get('http://localhost:5176')
html = response.text

# 查找所有 JS 文件引用
js_files = re.findall(r'script[^>]+src=["\']([^"\']+\.js[^"\']*)["\']', html)

print('=' * 60)
print('检查前端页面中的通知相关代码')
print('=' * 60)
print(f'\n找到 {len(js_files)} 个 JS 文件')

# 查找通知相关代码
for js_file in js_files[:5]:  # 检查前 5 个
    if 'assets' in js_file:
        url = f'http://localhost:5176{js_file}'
        try:
            js_response = requests.get(url, timeout=5)
            content = js_response.text
            
            # 搜索通知相关关键词
            if 'Notification' in content or '通知' in content or '铃铛' in content:
                print(f'\n在 {js_file} 中找到通知相关代码')
                
                # 提取相关代码段
                matches = re.findall(r'.{50}Notification.{100}', content[:5000])
                for match in matches[:3]:
                    print(f'  - ...{match}...')
        except:
            pass

print('\n' + '=' * 60)
print('建议：打开浏览器 F12 控制台查看具体错误信息')
print('=' * 60)
