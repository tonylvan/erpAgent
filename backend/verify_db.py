"""
Verify database tables and data
"""
import sys
sys.path.insert(0, 'D:\\erpAgent\\backend')

from sqlalchemy import create_engine, text, inspect
from app.db.database import DATABASE_URL

engine = create_engine(DATABASE_URL)

print("=" * 60)
print("DATABASE VERIFICATION")
print("=" * 60)

# Check tables
inspector = inspect(engine)
tables = inspector.get_table_names()
print(f"\nTables: {tables}")

# Check alerts table structure
if 'alerts' in tables:
    print("\n--- alerts table columns ---")
    columns = inspector.get_columns('alerts')
    for col in columns:
        print(f"  - {col['name']}: {col['type']}")
    
    # Check data
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM alerts"))
        count = result.fetchone()[0]
        print(f"\nTotal alerts: {count}")
        
        # Show sample data
        if count > 0:
            print("\n--- Sample alerts ---")
            result = conn.execute(text("""
                SELECT id, title, level, status, business_module, created_at 
                FROM alerts 
                ORDER BY created_at DESC 
                LIMIT 5
            """))
            for row in result.fetchall():
                print(f"  [{row.level}] {row.title} ({row.status})")
else:
    print("ERROR: alerts table not found!")

print("\n" + "=" * 60)
print("VERIFICATION COMPLETE")
print("=" * 60)
