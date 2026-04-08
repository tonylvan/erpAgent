from neo4j import GraphDatabase

driver = GraphDatabase.driver('bolt://localhost:7687', auth=('neo4j', 'Tony1985'))
session = driver.session()

# Test 1: Sales trend query
print("=== Test 1: Sales Trend ===")
result = session.run("""
MATCH (s:Sale)-[:HAS_TIME]->(t:Time)
WHERE t.week = date().week
RETURN t.day as day, sum(s.amount) as amount, count(s) as count
ORDER BY t.day
""")
rows = [dict(r) for r in result]
print(f"Found {len(rows)} rows")
for row in rows:
    print(row)

# Test 2: All sales with time
print("\n=== Test 2: All Sales with Time ===")
result = session.run("""
MATCH (s:Sale)-[:HAS_TIME]->(t:Time)
RETURN t.day as day, t.week as week, s.amount as amount
LIMIT 5
""")
rows = [dict(r) for r in result]
print(f"Found {len(rows)} rows")
for row in rows:
    print(row)

# Test 3: Current week number
print("\n=== Test 3: Current Week ===")
result = session.run("RETURN date().week as current_week")
row = result.single()
print(f"Current week: {row['current_week']}")

# Test 4: Sales data exists?
print("\n=== Test 4: Sales Count ===")
result = session.run("MATCH (s:Sale) RETURN count(s) as count")
row = result.single()
print(f"Total Sales: {row['count']}")

driver.close()