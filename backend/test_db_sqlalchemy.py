"""
Test database connection with URL
"""
from sqlalchemy import create_engine, text
import os

# Get database URL from environment
db_url = "postgresql://postgres:Tony1985@localhost:5432/erpagent"

print(f"Testing connection to: {db_url}")

try:
    engine = create_engine(db_url)
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        print("Database connection: SUCCESS")
        print("Query result:", result.fetchone())
except Exception as e:
    print(f"Connection failed: {e}")
    print("\nTrying to connect to postgres database...")
    try:
        engine = create_engine("postgresql://postgres:Tony1985@localhost:5432/postgres")
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            print("Postgres database connection: SUCCESS")
    except Exception as e2:
        print(f"Postgres connection also failed: {e2}")
