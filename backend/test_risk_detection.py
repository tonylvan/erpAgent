# -*- coding: utf-8 -*-
"""
端到端测试 - 验证风险检测功能
测试注入的异常数据是否被正确检测
"""

import requests
import json
from datetime import datetime

# API 配置
BASE_URL = "http://localhost:8005"

def test_business_risk():
    """测试业务风险检测"""
    print("\n" + "="*70)
    print("[1/3] 测试业务风险检测 Agent")
    print("="*70)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/agents/business-risk",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] API 调用成功")
            print(f"  检测到风险数量：{len(data.get('findings', []))}")
            
            # 检查是否检测到负库存
            findings = data.get('findings', [])
            for finding in findings:
                risk_type = finding.get('risk_type', '')
                severity = finding.get('severity', '')
                description = finding.get('description', '')
                
                print(f"\n  风险类型：{risk_type}")
                print(f"  严重程度：{severity}")
                print(f"  描述：{description}")
                
                # 检查是否包含我们的测试数据
                if '999999' in str(finding) or '负库存' in str(finding):
                    print(f"  ✅ 检测到负库存测试数据！")
                    
        else:
            print(f"  [ERROR] API 调用失败：{response.status_code}")
            print(f"  响应：{response.text[:200]}")
            
    except Exception as e:
        print(f"  [ERROR] 异常：{e}")

def test_financial_risk():
    """测试财务风险检测"""
    print("\n" + "="*70)
    print("[2/3] 测试财务风险检测 Agent")
    print("="*70)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/agents/financial-risk",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] API 调用成功")
            print(f"  检测到风险数量：{len(data.get('findings', []))}")
            
            # 检查是否检测到异常付款
            findings = data.get('findings', [])
            for finding in findings:
                risk_type = finding.get('risk_type', '')
                severity = finding.get('severity', '')
                description = finding.get('description', '')
                amount = finding.get('data', {}).get('amount', 'N/A')
                
                print(f"\n  风险类型：{risk_type}")
                print(f"  严重程度：{severity}")
                print(f"  描述：{description}")
                print(f"  金额：${amount:,.2f}" if isinstance(amount, (int, float)) else f"  金额：{amount}")
                
                # 检查是否包含我们的测试数据 (1.5 亿美元)
                if '888888' in str(finding) or (isinstance(amount, (int, float)) and amount > 100000000):
                    print(f"  ✅ 检测到异常付款测试数据！")
                    
        else:
            print(f"  [ERROR] API 调用失败：{response.status_code}")
            print(f"  响应：{response.text[:200]}")
            
    except Exception as e:
        print(f"  [ERROR] 异常：{e}")

def test_all_risks():
    """测试全量风险检测"""
    print("\n" + "="*70)
    print("[3/3] 测试全量风险检测")
    print("="*70)
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/v1/agents/all",
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"  [OK] API 调用成功")
            
            business_count = len(data.get('business_risk', []))
            financial_count = len(data.get('financial_risk', []))
            user_op_count = len(data.get('user_operation', []))
            
            print(f"\n  业务风险：{business_count} 条")
            print(f"  财务风险：{financial_count} 条")
            print(f"  用户操作风险：{user_op_count} 条")
            print(f"  总计：{business_count + financial_count + user_op_count} 条")
            
            # 保存测试结果
            with open('e2e_test_result.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'timestamp': datetime.now().isoformat(),
                    'test_result': data,
                    'summary': {
                        'business_risk': business_count,
                        'financial_risk': financial_count,
                        'user_operation': user_op_count,
                        'total': business_count + financial_count + user_op_count
                    }
                }, f, ensure_ascii=False, indent=2)
            
            print(f"\n  [OK] 测试结果已保存到 e2e_test_result.json")
            
        else:
            print(f"  [ERROR] API 调用失败：{response.status_code}")
            print(f"  响应：{response.text[:200]}")
            
    except Exception as e:
        print(f"  [ERROR] 异常：{e}")

# 主函数
if __name__ == '__main__':
    print("="*70)
    print("端到端测试 - 风险检测功能验证")
    print("="*70)
    print(f"API 地址：{BASE_URL}")
    print(f"测试时间：{datetime.now()}")
    
    test_business_risk()
    test_financial_risk()
    test_all_risks()
    
    print("\n" + "="*70)
    print("测试完成！")
    print("="*70)
