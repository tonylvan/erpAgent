"""
Seed tickets table with sample data
"""
import sys
sys.path.insert(0, 'D:\\erpAgent\\backend')

from app.db.database import get_db
from app.models.ticket import Ticket
from datetime import datetime, timedelta

def seed_tickets():
    """Add sample tickets"""
    print("Seeding tickets...")
    
    db = next(get_db())
    
    sample_tickets = [
        {
            "title": "ERP 系统登录失败",
            "status": "OPEN",
            "priority": "HIGH",
            "category": "IT Support",
            "description": "用户无法登录 ERP 系统，提示密码错误",
            "created_by": "zhangsan@company.com"
        },
        {
            "title": "财务报表导出异常",
            "status": "IN_PROGRESS",
            "priority": "MEDIUM",
            "category": "Finance",
            "description": "月度财务报表导出时出现乱码",
            "created_by": "lisi@company.com",
            "assigned_to": "support@company.com"
        },
        {
            "title": "库存数据不同步",
            "status": "OPEN",
            "priority": "URGENT",
            "category": "Warehouse",
            "description": "WMS 与 ERP 库存数据不一致，差异 15%",
            "created_by": "wangwu@company.com"
        },
        {
            "title": "采购订单审批流程优化",
            "status": "RESOLVED",
            "priority": "LOW",
            "category": "Procurement",
            "description": "建议简化采购订单审批流程",
            "created_by": "zhaoliu@company.com",
            "assigned_to": "manager@company.com",
            "resolved_at": datetime.now() - timedelta(days=2),
            "resolved_by": "manager@company.com"
        },
        {
            "title": "销售人员权限配置",
            "status": "CLOSED",
            "priority": "MEDIUM",
            "category": "Sales",
            "description": "为新销售人员配置 CRM 访问权限",
            "created_by": "hr@company.com",
            "assigned_to": "it@company.com",
            "resolved_at": datetime.now() - timedelta(days=5),
            "resolved_by": "it@company.com"
        },
    ]
    
    for ticket_data in sample_tickets:
        ticket = Ticket(**ticket_data)
        db.add(ticket)
    
    db.commit()
    
    total = db.query(Ticket).count()
    print(f"SUCCESS: {len(sample_tickets)} tickets added!")
    print(f"Total tickets in database: {total}")

if __name__ == "__main__":
    seed_tickets()
