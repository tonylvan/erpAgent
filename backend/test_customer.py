from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI", "bolt://localhost:7687"),
    auth=(os.getenv("NEO4J_USER", "neo4j"), os.getenv("NEO4J_PASSWORD"))
)

session = driver.session()

# Test 1: Check Customer nodes
print("=== Test 1: Customer nodes ===")
result = session.run("MATCH (c:Customer) RETURN c.name as name, c.code as code LIMIT 5")
rows = [dict(r) for r in result]
print(f"Found {len(rows)} Customer nodes")
for r in rows:
    print(f"  {r}")

# Test 2: Check MADE_TO relationships
print("\n=== Test 2: MADE_TO relationships ===")
result = session.run("""
    MATCH (c:Customer)<-[:MADE_TO]-(s:Sale)
    RETURN c.name as customer, sum(s.amount) as total, count(s) as order_count
    ORDER BY total DESC
    LIMIT 10
""")
rows = [dict(r) for r in result]
print(f"Found {len(rows)} rows")
for r in rows:
    print(f"  {r}")

# Test 3: Check Payment nodes with customer info
print("\n=== Test 3: Payment nodes ===")
result = session.run("""
    MATCH (p:Payment)
    RETURN p.id as id, p.customer as customer, p.amount as amount, p.status as status
    LIMIT 10
""")
rows = [dict(r) for r in result]
print(f"Found {len(rows)} Payment nodes")
for r in rows:
    print(f"  {r}")

# Test 4: Alternative - Sales with customer relationships
print("\n=== Test 4: Sales-Customer relationships ===")
result = session.run("""
    MATCH (s:Sale)-[r:MADE_TO]->(c:Customer)
    RETURN type(r) as rel_type, count(*) as count
""")
rows = [dict(r) for r in result]
print(f"Relationship summary: {rows}")

driver.close()