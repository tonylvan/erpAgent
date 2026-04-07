"""
GSD Platform Sample Data Creator
Creates sample alerts, tickets, and other test data
"""
import sys
import os
from datetime import datetime, timedelta

# Add project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.db.database import engine, get_db
from app.models.alert import Alert, AlertLevel, AlertStatus

def create_sample_alerts(db: Session):
    """Create sample alert data"""
    
    sample_alerts = [
        # Business Alerts
        Alert(
            title="Inventory Alert - Product A001",
            level=AlertLevel.MEDIUM,
            status=AlertStatus.UNREAD,
            business_module="Inventory Management",
            description="Product A001 inventory below safety line. Current: 50, Safety: 100",
            created_at=datetime.now() - timedelta(hours=2)
        ),
        Alert(
            title="Zero Inventory Alert - Product B002",
            level=AlertLevel.HIGH,
            status=AlertStatus.UNREAD,
            business_module="Inventory Management",
            description="Product B002 inventory is zero, immediate replenishment needed",
            created_at=datetime.now() - timedelta(hours=5)
        ),
        Alert(
            title="Payment Overdue Alert - Invoice INV-2026-001",
            level=AlertLevel.HIGH,
            status=AlertStatus.READ,
            business_module="Finance Management",
            description="Invoice INV-2026-001 payment overdue 15 days, amount: 50000",
            created_at=datetime.now() - timedelta(days=1),
            acknowledged_by="Zhang San",
            acknowledged_at=datetime.now() - timedelta(hours=12)
        ),
        Alert(
            title="Customer Churn Alert - ABC Corp",
            level=AlertLevel.MEDIUM,
            status=AlertStatus.UNREAD,
            business_module="Customer Management",
            description="Customer ABC Corp no order for 95 days, churn risk",
            created_at=datetime.now() - timedelta(days=2)
        ),
        Alert(
            title="Supplier Delivery Delay - PO-2026-045",
            level=AlertLevel.LOW,
            status=AlertStatus.READ,
            business_module="Procurement Management",
            description="Supplier XYZ Company PO-2026-045 delivery delayed 3 days",
            created_at=datetime.now() - timedelta(days=3),
            acknowledged_by="Li Si",
            acknowledged_at=datetime.now() - timedelta(days=1)
        ),
        Alert(
            title="Sales Order Anomaly - SO-2026-1234",
            level=AlertLevel.MEDIUM,
            status=AlertStatus.UNREAD,
            business_module="Sales Management",
            description="Order SO-2026-1234 amount anomaly, 200% above average",
            created_at=datetime.now() - timedelta(hours=8)
        ),
        
        # Financial Risk Alerts
        Alert(
            title="Cash Flow Alert",
            level=AlertLevel.CRITICAL,
            status=AlertStatus.UNREAD,
            business_module="Finance Management",
            description="Cash flow below safety line. Available: 120000, Safety: 200000",
            created_at=datetime.now() - timedelta(hours=1)
        ),
        Alert(
            title="Accounts Receivable Overdue Alert",
            level=AlertLevel.HIGH,
            status=AlertStatus.UNREAD,
            business_module="Finance Management",
            description="Customer DEF Corp AR overdue 30 days, amount: 180000",
            created_at=datetime.now() - timedelta(days=5)
        ),
        Alert(
            title="Accounts Payable Risk Alert",
            level=AlertLevel.MEDIUM,
            status=AlertStatus.READ,
            business_module="Finance Management",
            description="AP due in 7 days total: 350000, please arrange funds",
            created_at=datetime.now() - timedelta(days=1),
            acknowledged_by="Wang Wu",
            acknowledged_at=datetime.now() - timedelta(hours=6)
        ),
        Alert(
            title="Financial Ratio Anomaly Alert",
            level=AlertLevel.MEDIUM,
            status=AlertStatus.UNREAD,
            business_module="Finance Management",
            description="Current ratio 1.2 < standard 2.0, Debt-to-equity 2.5 > standard 1.5",
            created_at=datetime.now() - timedelta(days=7)
        ),
        Alert(
            title="Budget Variance Alert - Marketing Dept",
            level=AlertLevel.LOW,
            status=AlertStatus.READ,
            business_module="Budget Management",
            description="Marketing Dept Q1 budget variance 25%, exceeds threshold 20%",
            created_at=datetime.now() - timedelta(days=10),
            acknowledged_by="Zhao Liu",
            acknowledged_at=datetime.now() - timedelta(days=5)
        ),
    ]
    
    # Add to database
    db.add_all(sample_alerts)
    db.commit()
    
    print(f"Created {len(sample_alerts)} sample alerts")
    
    return len(sample_alerts)


def main():
    """Main entry point"""
    print("=" * 70)
    print("GSD Platform - Sample Data Creator")
    print("=" * 70)
    
    try:
        # Create database session
        db = Session(bind=engine)
        
        # Create sample alerts
        alert_count = create_sample_alerts(db)
        
        print("=" * 70)
        print(f"Sample data creation completed!")
        print(f"Total alerts created: {alert_count}")
        print("=" * 70)
        
        db.close()
        
    except Exception as e:
        print(f"Error creating sample data: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
