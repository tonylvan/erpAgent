from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD"))
)

session = driver.session()

# Test 1: Sales trend
print("=== Test 1: Sales Trend ===")
result = session.run("""
    MATCH (s:Sale)-[:HAS_TIME]->(t:Time)
    WHERE (t.week = date().week OR t.week = date().week - 1 OR t.week >= date().week - 2)
    RETURN t.day as day, sum(s.amount) as amount, count(s) as count
    ORDER BY t.day
""")
rows = [dict(r) for r in result]
print(f"Found {len(rows)} rows")
for r in rows[:3]:
    print(f"  {r}")

# Test 2: Customer ranking
print("\n=== Test 2: Customer Ranking ===")
result = session.run("""
    MATCH (c:Customer)-[:PURCHASED]->(o:Order)
    WHERE o.date >= date() - duration({days: 30})
    RETURN c.name as customer, sum(o.amount) as total, count(o) as order_count
    ORDER BY total DESC
    LIMIT 10
""")
rows = [dict(r) for r in result]
print(f"Found {len(rows)} rows")

# Try alternative customer query
print("\n=== Test 3: Alternative Customer Query ===")
result = session.run("""
    MATCH (c:Customer)<-[:MADE_TO]-(s:Sale)
    RETURN c.name as customer, sum(s.amount) as total, count(s) as order_count
    ORDER BY total DESC
    LIMIT 10
""")
rows = [dict(r) for r in result]
print(f"Found {len(rows)} rows")
for r in rows[:3]:
    print(f"  {r}")

driver.close()