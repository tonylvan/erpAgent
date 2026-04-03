"""API 测试脚本 - 验证核心功能。"""

import asyncio
import httpx


BASE_URL = "http://localhost:8000"


async def test_health():
    """测试健康检查。"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/health")
        print(f"✅ 健康检查：{resp.status_code}")
        print(f"   响应：{resp.json()}")
        return resp.status_code == 200


async def test_login():
    """测试登录。"""
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            f"{BASE_URL}/api/v1/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        print(f"✅ 登录：{resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"   Token 类型：{data.get('token_type')}")
            print(f"   过期时间：{data.get('expires_in')}s")
            return data.get("access_token")
        return None


async def test_get_me(token: str):
    """测试获取当前用户。"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        print(f"✅ 获取用户：{resp.status_code}")
        if resp.status_code == 200:
            print(f"   用户：{resp.json()}")
        return resp.status_code == 200


async def test_tables(token: str):
    """测试获取表列表。"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/api/v1/data/tables",
            headers={"Authorization": f"Bearer {token}"},
        )
        print(f"✅ 获取表列表：{resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            print(f"   表数量：{data.get('count', 0)}")
        return resp.status_code == 200


async def test_graph_ontology(token: str):
    """测试获取图谱。"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            f"{BASE_URL}/api/v1/graph/ontology?mode=schema",
            headers={"Authorization": f"Bearer {token}"},
        )
        print(f"✅ 获取图谱：{resp.status_code}")
        if resp.status_code == 200:
            data = resp.json()
            if data.get("success"):
                graph = data.get("data", {})
                print(f"   节点数：{graph.get('meta', {}).get('node_count', 0)}")
                print(f"   边数：{graph.get('meta', {}).get('edge_count', 0)}")
        return resp.status_code == 200


async def test_websocket_stats():
    """测试 WebSocket 统计。"""
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{BASE_URL}/api/v1/ws/stats")
        print(f"✅ WebSocket 统计：{resp.status_code}")
        if resp.status_code == 200:
            print(f"   响应：{resp.json()}")
        return resp.status_code == 200


async def main():
    """运行所有测试。"""
    print("=" * 60)
    print("GSD 后端 API 测试")
    print("=" * 60)
    print()
    
    results = []
    
    # 1. 健康检查
    print("[1/6] 健康检查...")
    results.append(await test_health())
    print()
    
    # 2. 登录
    print("[2/6] 登录...")
    token = await test_login()
    if not token:
        print("❌ 登录失败，终止测试")
        return
    print()
    
    # 3. 获取用户
    print("[3/6] 获取当前用户...")
    results.append(await test_get_me(token))
    print()
    
    # 4. 获取表列表
    print("[4/6] 获取表列表...")
    results.append(await test_tables(token))
    print()
    
    # 5. 获取图谱
    print("[5/6] 获取图谱...")
    results.append(await test_graph_ontology(token))
    print()
    
    # 6. WebSocket 统计
    print("[6/6] WebSocket 统计...")
    results.append(await test_websocket_stats())
    print()
    
    # 总结
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"测试结果：{passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！")
    else:
        print(f"⚠️  {total - passed} 个测试失败")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
