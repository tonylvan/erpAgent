# -*- coding: utf-8 -*-
import requests
import json
import sys

# Force UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

url = 'http://localhost:8007/api/v1/smart-query-agent/query'

print("=" * 60)
print("测试：OpenClaw HTTP API 模式")
print("=" * 60)

# 测试查询
data = {'query': '本周销售趋势', 'session_id': 'test-http-001'}
print(f"\n发送查询：{data['query']}")

try:
    print(f"[DEBUG] POST {url}")
    print(f"[DEBUG] Payload: {json.dumps(data, ensure_ascii=False)}")
    
    response = requests.post(url, json=data, timeout=60)
    print(f"[DEBUG] Response Status: {response.status_code}")
    
    result = response.json()
    
    # Save raw response to file for inspection
    with open('D:\\erpAgent\\backend\\test_response.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n[INFO] 完整响应已保存到 D:\\erpAgent\\backend\\test_response.json")
    
    print(f"\n[OK] Success: {result['success']}")
    print(f"DataType: {result['data_type']}")
    print(f"Agent Model: {result['agent_model']}")
    
    if result['data'] and isinstance(result['data'], list) and len(result['data']) > 0:
        print(f"\n[OK] 真实 Neo4j 数据！Count: {len(result['data'])}")
        print(f"Data preview:")
        print(json.dumps(result['data'][:2], ensure_ascii=False, indent=2))
    else:
        print(f"\nData: {result['data']}")
    
    print(f"\n[Answer]:")
    try:
        print(result['answer'][:300] + "...")
    except UnicodeEncodeError:
        print("(Answer contains Unicode characters - skipped display)")
        print(f"Answer length: {len(result['answer'])} chars")
    
    print(f"\n[Reasoning]:")
    try:
        for step in result.get('reasoning_process', [])[:3]:
            print(f"  {step}")
    except UnicodeEncodeError:
        print("(Reasoning contains Unicode characters - skipped display)")
        print(f"Reasoning steps: {len(result.get('reasoning_process', []))}")
    
    print(f"\n[Follow-up]:")
    try:
        for q in result.get('follow_up', [])[:3]:
            print(f"  - {q}")
    except UnicodeEncodeError:
        print("(Follow-up contains Unicode characters - skipped display)")
        print(f"Follow-up questions: {len(result.get('follow_up', []))}")
    
except requests.exceptions.Timeout:
    print("[ERROR] 请求超时（>60 秒）")
except Exception as e:
    print(f"[ERROR] 错误：{e}")

print("\n" + "=" * 60)
print("[DONE] 测试完成！")
print("=" * 60)
