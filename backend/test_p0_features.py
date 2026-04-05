import requests
import json

print('='*70)
print('P0 功能测试 - JWT 认证 + 智能问数')
print('='*70)

API = 'http://localhost:8005'

# 1. 测试登录
print('\n[1] 用户登录...')
try:
    r = requests.post(f'{API}/api/v1/auth/login', 
                      json={'username': 'admin', 'password': 'admin123'},
                      timeout=5)
    print(f'    状态：{r.status_code}')
    if r.status_code == 200:
        data = r.json()
        token = data.get('access_token', '')
        print(f'    Token: {token[:60]}...')
        print(f'    Token 类型：{data.get("token_type")}')
        
        # 2. 测试获取用户信息
        print('\n[2] 获取用户信息...')
        headers = {'Authorization': f'Bearer {token}'}
        r = requests.get(f'{API}/api/v1/auth/me', headers=headers, timeout=5)
        print(f'    状态：{r.status_code}')
        if r.status_code == 200:
            user = r.json()
            print(f'    用户：{json.dumps(user, indent=2, ensure_ascii=False)}')
        else:
            print(f'    错误：{r.text[:100]}')
        
        # 3. 测试智能问数（带认证）
        print('\n[3] 智能问数（带认证）...')
        r = requests.post(
            f'{API}/api/v1/smart-query-v40/query',
            json={'query': '你好', 'session_id': 'test'},
            headers=headers,
            timeout=10
        )
        print(f'    状态：{r.status_code}')
        if r.status_code == 200:
            result = r.json()
            print(f'    成功：{result.get("success")}')
            print(f'    路由：{result.get("route")}')
            print(f'    回答：{result.get("answer", "")[:50]}...')
        else:
            print(f'    错误：{r.text[:100]}')
    else:
        print(f'    错误：{r.text[:200]}')
except Exception as e:
    print(f'失败：{e}')

print('\n' + '='*70)
print('测试完成')
print('='*70)
