import asyncio
import sys
sys.path.insert(0, '.')

from app.api.v1.smart_query_v2 import Neo4jKnowledgeEngine

async def test():
    engine = Neo4jKnowledgeEngine()
    
    # Test query
    question = "本周销售趋势"
    print(f"Testing: {question}")
    
    # Get Cypher
    cypher = await engine._nl2cypher(question)
    print(f"Cypher: {cypher}")
    
    # Execute
    result = await engine._execute_cypher(cypher)
    print(f"Result: {len(result)} rows")
    for r in result[:3]:
        print(f"  {r}")
    
    # Fallback
    if not result:
        fallback = await engine._fallback_query(question)
        print(f"Fallback: {len(fallback)} rows")
        for r in fallback[:3]:
            print(f"  {r}")

asyncio.run(test())