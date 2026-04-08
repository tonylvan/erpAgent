import asyncio
import sys
sys.path.insert(0, '.')

from app.api.v1.smart_query_v2 import Neo4jKnowledgeEngine

async def test():
    engine = Neo4jKnowledgeEngine()
    
    # Test full query
    question = "本周销售趋势"
    print(f"Testing full query: {question}")
    
    result = await engine.query(question)
    
    print(f"Success: {result.get('success')}")
    print(f"Data Type: {result.get('data_type')}")
    print(f"Has Chart Config: {result.get('chart_config') is not None}")
    print(f"Has Data: {result.get('data') is not None}")
    
    if result.get('chart_config'):
        print(f"Chart type: {result.get('chart_config', {}).get('chart', {}).get('type')}")

asyncio.run(test())