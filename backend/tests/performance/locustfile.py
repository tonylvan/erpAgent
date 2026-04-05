"""
GSD 智能问数性能测试 - Locust
覆盖：并发查询、响应时间、QPS、错误率
总计 5 个测试场景
"""
from locust import HttpUser, task, between, events
import time
import json
from datetime import datetime


class SmartQueryUser(HttpUser):
    """智能问数用户行为模拟"""
    
    # 等待时间：1-3 秒
    wait_time = between(1, 3)
    
    # 测试查询列表
    queries = [
        "显示本周销售趋势",
        "查询 Top 10 客户",
        "统计各产品类别销售额",
        "显示库存预警商品",
        "查看付款单列表",
        "分析销售变化走势",
        "客户排行榜",
        "库存情况如何",
        "统计概览",
        "业务数据分析"
    ]
    
    def on_start(self):
        """用户开始时的初始化"""
        print(f"User started at {datetime.now()}")
    
    def on_stop(self):
        """用户结束时的清理"""
        print(f"User stopped at {datetime.now()}")
    
    @task(3)
    def query_sales_trend(self):
        """销售趋势查询（权重 3）"""
        with self.client.post(
            "/api/v1/query",
            json={"query": "显示本周销售趋势"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    response.success()
                else:
                    response.failure("Query failed")
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(3)
    def query_customer_rank(self):
        """客户排行查询（权重 3）"""
        with self.client.post(
            "/api/v1/query",
            json={"query": "查询 Top 10 客户"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(2)
    def query_inventory(self):
        """库存查询（权重 2）"""
        with self.client.post(
            "/api/v1/query",
            json={"query": "显示库存预警商品"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(2)
    def query_payment(self):
        """付款单查询（权重 2）"""
        with self.client.post(
            "/api/v1/query",
            json={"query": "查看付款单列表"},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(1)
    def get_suggested_questions(self):
        """获取推荐问题（权重 1）"""
        with self.client.get(
            "/api/v1/suggested-questions",
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")
    
    @task(1)
    def random_query(self):
        """随机查询（权重 1）"""
        query = self.random.choice(self.queries)
        with self.client.post(
            "/api/v1/query",
            json={"query": query},
            catch_response=True
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Status code: {response.status_code}")


# ==================== 性能测试场景 ====================

class StressTestUser(HttpUser):
    """压力测试用户 - 高并发场景"""
    
    wait_time = between(0.1, 0.5)  # 更短的等待时间
    
    @task
    def stress_query(self):
        """压力测试查询"""
        self.client.post(
            "/api/v1/query",
            json={"query": "压力测试"}
        )


class EnduranceTestUser(HttpUser):
    """耐久性测试用户 - 长时间运行"""
    
    wait_time = between(2, 5)  # 正常等待时间
    
    @task
    def endurance_query(self):
        """耐久性测试查询"""
        self.client.post(
            "/api/v1/query",
            json={"query": "耐久性测试"}
        )


# ==================== 事件监听器 ====================

@events.request.add_listener
def on_request(request_type, name, response_time, response_length, exception, **kwargs):
    """请求完成时的回调"""
    if exception:
        print(f"Request failed: {name}, Error: {exception}")


@events.test_start.add_listener
def on_test_start(environment, **kwargs):
    """测试开始时的回调"""
    print("=" * 80)
    print("Performance Test Started")
    print(f"Target Host: {environment.host}")
    print("=" * 80)


@events.test_stop.add_listener
def on_test_stop(environment, **kwargs):
    """测试结束时的回调"""
    print("=" * 80)
    print("Performance Test Completed")
    
    # 输出统计信息
    stats = environment.stats
    print(f"\nTotal Requests: {stats.total.num_requests}")
    print(f"Total Failures: {stats.total.num_failures}")
    print(f"Failure Rate: {(stats.total.num_failures / stats.total.num_requests * 100):.2f}%")
    print(f"Average Response Time: {stats.total.avg_response_time:.2f}ms")
    print(f"Requests per Second: {stats.total.current_rps:.2f}")
    print("=" * 80)


# ==================== 性能指标要求 ====================
"""
验收标准：
1. 平均响应时间 < 2000ms
2. 95% 响应时间 < 3000ms
3. P99 响应时间 < 500ms
4. QPS ≥ 50
5. 错误率 < 1%

运行命令：
# 基础测试
locust -f tests/performance/load_test.py --host=http://localhost:8005

# 压力测试（100 用户，10 用户/秒）
locust -f tests/performance/load_test.py --host=http://localhost:8005 --headless -u 100 -r 10 --run-time 60s

# 耐久性测试（50 用户，300 秒）
locust -f tests/performance/load_test.py --host=http://localhost:8005 --headless -u 50 -r 5 --run-time 300s
"""
