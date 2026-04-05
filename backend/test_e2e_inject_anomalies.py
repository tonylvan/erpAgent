# -*- coding: utf-8 -*-
"""
端到端测试 - 注入异常数据
测试场景:
1. 负库存交易
2. 异常大额付款 (1.5 亿美元)
3. 天价采购订单 (英伟达芯片 19 万美金/个)
"""

import psycopg2
from datetime import datetime
from decimal import Decimal

# 数据库配置
PG_CONFIG = {
    'host': 'localhost',
    'port': 5432,
    'database': 'erp',
    'user': 'postgres',
    'password': 'postgres'
}

def get_connection():
    return psycopg2.connect(**PG_CONFIG)

# 1. 创建负库存交易
def create_negative_inventory():
    print("\n[1/3] 创建负库存交易...")
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # 删除旧数据
        cur.execute("DELETE FROM mtl_material_transactions WHERE transaction_id = %s", (-888888,))
        cur.execute("DELETE FROM mtl_system_items_b WHERE inventory_item_id = %s AND organization_id = %s", (999999, 1))
        
        # 创建测试商品 (使用 mtl_system_items_b)
        product_id = 999999
        cur.execute("""
            INSERT INTO mtl_system_items_b 
            (inventory_item_id, organization_id, segment1, description, inventory_item_status_code, primary_uom_code, creation_date, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (product_id, 1, 'NEG-TEST-001', '负库存测试商品 - 英伟达 H100 芯片', 'ACTIVE', 'Ea', datetime.now(), 1))
        
        # 创建负库存交易 (使用 mtl_material_transactions)
        transaction_id = -888888
        cur.execute("""
            INSERT INTO mtl_material_transactions 
            (transaction_id, transaction_type_id, transaction_date, organization_id, 
             inventory_item_id, transaction_quantity, primary_quantity, transaction_reference, distribution_account_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            transaction_id,
            1,  # transaction_type_id
            datetime.now(),
            1,  # organization_id
            product_id,
            -100,  # 负库存！
            -100,  # primary_quantity
            '负库存测试',
            1  # distribution_account_id
        ))
        
        conn.commit()
        print(f"  [OK] 创建负库存商品：ID={product_id}")
        print(f"  [OK] 创建负库存交易：ID={transaction_id}, 数量=-100")
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

# 2. 创建异常大额付款 (1.5 亿美元)
def create_huge_payment():
    print("\n[2/3] 创建异常大额付款...")
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # 删除旧数据
        cur.execute("DELETE FROM ap_payments_all WHERE check_id = %s", (-666666,))
        cur.execute("DELETE FROM ap_invoices_all WHERE invoice_id = %s", (-777777,))
        cur.execute("DELETE FROM ap_suppliers WHERE vendor_id = %s", (888888,))
        
        # 创建测试供应商
        vendor_id = 888888
        cur.execute("""
            INSERT INTO ap_suppliers (vendor_id, segment1, vendor_name, status)
            VALUES (%s, %s, %s, %s)
        """, (vendor_id, 'HUGE-PAY-001', '异常付款测试供应商 - 英伟达', 'ACTIVE'))
        
        # 创建测试发票 (1.5 亿美元)
        invoice_id = -777777
        cur.execute("""
            INSERT INTO ap_invoices_all 
            (invoice_id, invoice_num, vendor_id, invoice_amount, payment_status, invoice_date, due_date, creation_date, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            invoice_id,
            'HUGE-INV-001',
            vendor_id,
            Decimal('150000000.00'),  # 1.5 亿美元！
            'PENDING',
            datetime.now(),
            datetime.now(),
            datetime.now(),
            1
        ))
        
        # 创建付款 (1.5 亿美元)
        check_id = -666666
        cur.execute("""
            INSERT INTO ap_payments_all 
            (check_id, check_number, amount, check_date, status, vendor_id, bank_account_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        """, (
            check_id,
            'HUGE-PAY-001',
            Decimal('150000000.00'),  # 1.5 亿美元！
            datetime.now(),
            'PENDING',
            vendor_id,
            1
        ))
        
        conn.commit()
        print(f"  [OK] 创建测试供应商：ID={vendor_id}")
        print(f"  [OK] 创建测试发票：ID={invoice_id}, 金额=$150,000,000.00")
        print(f"  [OK] 创建付款：ID={check_id}, 金额=$150,000,000.00")
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

# 3. 创建天价采购订单 (英伟达芯片 19 万美金/个)
def create_expensive_po():
    print("\n[3/3] 创建天价采购订单...")
    
    conn = get_connection()
    cur = conn.cursor()
    
    try:
        # 删除旧数据
        cur.execute("DELETE FROM po_lines_all WHERE po_line_id = %s", (-444444,))
        cur.execute("DELETE FROM po_headers_all WHERE po_header_id = %s", (-555555,))
        
        # 使用上面创建的供应商
        vendor_id = 888888
        
        # 创建采购订单头 (1900 万美金)
        po_header_id = -555555
        cur.execute("""
            INSERT INTO po_headers_all 
            (po_header_id, segment1, type_lookup_code, status_lookup_code, vendor_id, amount, currency_code, 
             approved_flag, creation_date, approved_date, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            po_header_id,
            'EXP-PO-001',
            'STANDARD',
            'APPROVED',
            vendor_id,
            Decimal('19000000.00'),  # 1900 万美金 (100 个芯片 * 19 万/个)
            'USD',
            'Y',
            datetime.now(),
            datetime.now(),
            1
        ))
        
        # 创建采购订单行 (100 个芯片，单价 19 万美金)
        po_line_id = -444444
        cur.execute("""
            INSERT INTO po_lines_all 
            (po_line_id, po_header_id, line_num, item_description, unit_price, quantity, amount, currency_code)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            po_line_id,
            po_header_id,
            1,
            '英伟达 H100 芯片',  # item_description
            Decimal('190000.00'),  # 单价 19 万美金！
            100,  # 数量 100 个
            Decimal('19000000.00'),  # 总计 1900 万美金
            'USD'
        ))
        
        conn.commit()
        print(f"  [OK] 创建采购订单：ID={po_header_id}")
        print(f"  [OK] 采购订单行：ID={po_line_id}")
        print(f"  [OK] 商品：英伟达 H100 芯片")
        print(f"  [OK] 数量：100 个")
        print(f"  [OK] 单价：$190,000.00 (19 万美金)")
        print(f"  [OK] 总计：$19,000,000.00 (1900 万美金)")
        
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()

# 主函数
if __name__ == '__main__':
    print("="*70)
    print("端到端测试 - 注入异常数据")
    print("="*70)
    
    try:
        create_negative_inventory()
        create_huge_payment()
        create_expensive_po()
        
        print("\n" + "="*70)
        print("[OK] 所有异常数据注入完成！")
        print("="*70)
        
        print("\n测试数据汇总:")
        print("  1. 负库存商品：-100 个 (应该触发库存预警)")
        print("  2. 异常付款：$150,000,000.00 (应该触发付款异常)")
        print("  3. 天价采购：$190,000.00/个 (应该触发采购价格异常)")
        
        print("\n下一步:")
        print("  1. 访问 http://localhost:5181 查看预警中心")
        print("  2. 查看是否检测到这些异常")
        print("  3. 验证 Agent 检测规则是否正常工作")
        
    except Exception as e:
        print(f"\n[ERROR] 错误：{e}")
        import traceback
        traceback.print_exc()
