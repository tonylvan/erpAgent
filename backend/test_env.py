from pathlib import Path
from dotenv import load_dotenv
import os

# Simulate the path resolution
file_path = Path(__file__).resolve()
backend_root = file_path.parent
env_path = backend_root / '.env'

print(f'Backend root: {backend_root}')
print(f'Env path: {env_path}')
print(f'Env exists: {env_path.exists()}')

# Load .env
load_dotenv(env_path)

print(f'\nAfter load_dotenv:')
print(f'NEO4J_URI: {os.getenv("NEO4J_URI")}')
print(f'NEO4J_USER: {os.getenv("NEO4J_USER")}')
print(f'NEO4J_PASSWORD: {os.getenv("NEO4J_PASSWORD")}')

# Test connection
from neo4j import GraphDatabase
uri = os.getenv("NEO4J_URI")
user = os.getenv("NEO4J_USER")
password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(user, password))
with driver.session() as session:
    result = session.run("MATCH (n) RETURN count(n) as count")
    count = result.single()['count']
    print(f'\n[OK] Neo4j connected! Total nodes: {count}')
driver.close()