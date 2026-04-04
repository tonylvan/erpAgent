"""
Redis 缓存配置
"""
import redis
import json
import os
from typing import Any, Optional

class RedisCache:
    """Redis 缓存客户端"""
    
    def __init__(self):
        self.client = None
        self.enabled = False
        self._connect()
    
    def _connect(self):
        """连接 Redis"""
        try:
            host = os.getenv("REDIS_HOST", "localhost")
            port = int(os.getenv("REDIS_PORT", "6379"))
            password = os.getenv("REDIS_PASSWORD")
            
            self.client = redis.Redis(
                host=host,
                port=port,
                password=password,
                db=0,
                decode_responses=True,
                socket_connect_timeout=5
            )
            
            # 测试连接
            self.client.ping()
            self.enabled = True
            print(f"[OK] Redis 已连接：{host}:{port}")
        except Exception as e:
            print(f"[WARN] Redis 连接失败：{e}，使用内存缓存")
            self.enabled = False
            self.client = None
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.enabled or not self.client:
            return None
        
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return None
        except Exception as e:
            print(f"[ERROR] Redis get 错误：{e}")
            return None
    
    def set(self, key: str, value: Any, expire: int = 3600) -> bool:
        """设置缓存"""
        if not self.enabled or not self.client:
            return False
        
        try:
            data = json.dumps(value, ensure_ascii=False)
            self.client.setex(key, expire, data)
            return True
        except Exception as e:
            print(f"[ERROR] Redis set 错误：{e}")
            return False
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        if not self.enabled or not self.client:
            return False
        
        try:
            self.client.delete(key)
            return True
        except Exception as e:
            print(f"[ERROR] Redis delete 错误：{e}")
            return False
    
    def clear_pattern(self, pattern: str) -> bool:
        """批量删除匹配模式的缓存"""
        if not self.enabled or not self.client:
            return False
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                self.client.delete(*keys)
            return True
        except Exception as e:
            print(f"[ERROR] Redis clear_pattern 错误：{e}")
            return False
    
    def stats(self) -> dict:
        """获取 Redis 统计信息"""
        if not self.enabled or not self.client:
            return {"enabled": False}
        
        try:
            info = self.client.info("stats")
            db_size = self.client.dbsize()
            return {
                "enabled": True,
                "connected": True,
                "db_size": db_size,
                "total_commands_processed": info.get("total_commands_processed", 0),
                "keyspace_hits": info.get("keyspace_hits", 0),
                "keyspace_misses": info.get("keyspace_misses", 0),
            }
        except Exception as e:
            return {"enabled": False, "error": str(e)}


# 全局缓存实例
cache = RedisCache()
