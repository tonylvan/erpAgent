"""
GSD Platform - Create Sample Ticket Data
"""
import sys
import os
from datetime import datetime, timedelta

# Add project path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from sqlalchemy.orm import Session
from app.db.database import engine
from app.models.ticket import Ticket

def create_sample_tickets(db: Session):
    """Create sample ticket data"""
    
    sample_tickets = [
        Ticket(
            title="Follow up: Inventory Alert - Product A001",
            description="Customer reported inventory discrepancy for Product A001. Need to investigate stock levels.",
            status="OPEN",
            priority="HIGH",
            category="Inventory Management",
            created_by="system",
            assigned_to="Zhang San"
        ),
        Ticket(
            title="Payment Overdue Investigation - INV-2026-001",
            description="Invoice INV-2026-001 is 15 days overdue. Contact customer for payment status.",
            status="IN_PROGRESS",
            priority="HIGH",
            category="Finance Management",
            created_by="system",
            assigned_to="Li Si",
            created_at=datetime.now() - timedelta(days=2)
        ),
        Ticket(
            title="Customer Churn Prevention - ABC Corp",
            description="ABC Corp hasn't ordered in 95 days. Schedule account review meeting.",
            status="OPEN",
            priority="MEDIUM",
            category="Customer Management",
            created_by="system",
            assigned_to="Wang Wu"
        ),
        Ticket(
            title="Supplier Performance Review - XYZ Company",
            description="XYZ Company has delayed delivery 3 times in Q1. Conduct performance review.",
            status="CLOSED",
            priority="LOW",
            category="Procurement Management",
            created_by="system",
            assigned_to="Zhao Liu",
            created_at=datetime.now() - timedelta(days=5),
            resolved_at=datetime.now() - timedelta(days=1)
        ),
        Ticket(
            title="Cash Flow Optimization Plan",
            description="Current cash flow below safety line. Develop optimization strategy.",
            status="OPEN",
            priority="URGENT",
            category="Finance Management",
            created_by="system",
            assigned_to="Finance Team"
        ),
    ]
    
    # Add to database
    db.add_all(sample_tickets)
    db.commit()
    
    print(f"Created {len(sample_tickets)} sample tickets")
    
    return len(sample_tickets)


def main():
    """Main entry point"""
    print("=" * 70)
    print("GSD Platform - Sample Ticket Creator")
    print("=" * 70)
    
    try:
        db = Session(bind=engine)
        ticket_count = create_sample_tickets(db)
        
        print("=" * 70)
        print(f"Sample ticket creation completed!")
        print(f"Total tickets created: {ticket_count}")
        print("=" * 70)
        
        db.close()
        
    except Exception as e:
        print(f"Error creating sample tickets: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
