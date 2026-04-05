import requests

# 获取 OpenAPI schema
r = requests.get('http://localhost:8005/openapi.json')
if r.status_code == 200:
    schema = r.json()
    paths = list(schema.get('paths', {}).keys())
    
    print('可用的 API 路径:')
    print('='*70)
    for path in sorted(paths):
        if 'auth' in path.lower():
            print(f'  [认证] {path}')
        elif 'smart' in path.lower():
            print(f'  [问数] {path}')
        elif 'health' in path.lower() or path == '/':
            print(f'  [健康] {path}')
    print('='*70)
    print(f'总路径数：{len(paths)}')
else:
    print(f'获取 OpenAPI 失败：{r.status_code}')
