"""
Seed database with sample alert data
"""
import sys
sys.path.insert(0, 'D:\\erpAgent\\backend')

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.alert import Alert, AlertLevel, AlertStatus
from datetime import datetime, timedelta

from app.db.database import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

db = SessionLocal()

print("Seeding database with sample alerts...")

# Sample alerts
sample_alerts = [
    Alert(
        title="Critical Sales Anomaly Detected",
        level=AlertLevel.CRITICAL,
        status=AlertStatus.UNREAD,
        business_module="Sales",
        description="Sales dropped 45% in the last 24 hours. Immediate attention required.",
        created_at=datetime.now() - timedelta(hours=2)
    ),
    Alert(
        title="Inventory Level Below Safety Stock",
        level=AlertLevel.HIGH,
        status=AlertStatus.UNREAD,
        business_module="Warehouse",
        description="SKU-1234 quantity is below minimum threshold. Reorder recommended.",
        created_at=datetime.now() - timedelta(hours=5)
    ),
    Alert(
        title="Payment Overdue - ABC Corporation",
        level=AlertLevel.HIGH,
        status=AlertStatus.READ,
        business_module="Finance",
        description="Payment of $50,000 is 30 days overdue from ABC Corporation.",
        created_at=datetime.now() - timedelta(days=1)
    ),
    Alert(
        title="Production Line 3 Maintenance Due",
        level=AlertLevel.MEDIUM,
        status=AlertStatus.UNREAD,
        business_module="Production",
        description="Scheduled maintenance for Production Line 3 is due in 3 days.",
        created_at=datetime.now() - timedelta(hours=12)
    ),
    Alert(
        title="Employee Training Completion",
        level=AlertLevel.LOW,
        status=AlertStatus.ACKNOWLEDGED,
        business_module="HR",
        description="All employees in department have completed Q1 safety training.",
        created_at=datetime.now() - timedelta(days=2),
        acknowledged_by="admin",
        acknowledged_at=datetime.now() - timedelta(days=1)
    ),
]

# Add to database
db.add_all(sample_alerts)
db.commit()

print(f"SUCCESS: {len(sample_alerts)} alerts added to database!")

# Verify
count = db.query(Alert).count()
print(f"Total alerts in database: {count}")

db.close()

print("\nSeed data complete!")
