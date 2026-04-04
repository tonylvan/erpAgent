"""
ERP Agent 统一配置管理
========================
从环境变量和 .env 文件加载配置，提供类型安全的配置访问
"""
import os
from typing import Optional, List
from dataclasses import dataclass, field
from dotenv import load_dotenv

# 加载 .env 文件
load_dotenv()


@dataclass
class Neo4jConfig:
    """Neo4j 图数据库配置"""
    uri: str = field(default_factory=lambda: os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687"))
    user: str = field(default_factory=lambda: os.getenv("NEO4J_USER", "neo4j"))
    password: str = field(default_factory=lambda: os.getenv("NEO4J_PASSWORD", ""))
    database: str = field(default_factory=lambda: os.getenv("NEO4J_DATABASE", "neo4j"))
    
    # 超时配置（秒）
    timeout: int = field(default_factory=lambda: int(os.getenv("NEO4J_TIMEOUT", "20")))
    connection_timeout: int = field(default_factory=lambda: int(os.getenv("NEO4J_CONNECTION_TIMEOUT", "30")))
    max_connection_lifetime: int = field(default_factory=lambda: int(os.getenv("NEO4J_MAX_CONNECTION_LIFETIME", "3600")))
    max_connection_pool_size: int = field(default_factory=lambda: int(os.getenv("NEO4J_MAX_CONNECTION_POOL_SIZE", "50")))
    
    @property
    def is_configured(self) -> bool:
        """检查 Neo4j 是否正确配置"""
        return bool(self.password)
    
    def get_driver_params(self) -> dict:
        """获取 Neo4j 驱动参数"""
        return {
            "uri": self.uri,
            "auth": (self.user, self.password),
            "database": self.database,
            "max_connection_lifetime": self.max_connection_lifetime,
            "max_connection_pool_size": self.max_connection_pool_size,
        }


@dataclass
class PostgresConfig:
    """PostgreSQL 数据库配置"""
    host: str = field(default_factory=lambda: os.getenv("POSTGRES_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("POSTGRES_PORT", "5432")))
    database: str = field(default_factory=lambda: os.getenv("POSTGRES_DB", "erp"))
    user: str = field(default_factory=lambda: os.getenv("POSTGRES_USER", "postgres"))
    password: str = field(default_factory=lambda: os.getenv("POSTGRES_PASSWORD", "postgres"))
    
    # 连接池配置
    pool_size: int = field(default_factory=lambda: int(os.getenv("POSTGRES_POOL_SIZE", "10")))
    max_overflow: int = field(default_factory=lambda: int(os.getenv("POSTGRES_MAX_OVERFLOW", "20")))
    pool_timeout: int = field(default_factory=lambda: int(os.getenv("POSTGRES_POOL_TIMEOUT", "30")))
    pool_recycle: int = field(default_factory=lambda: int(os.getenv("POSTGRES_POOL_RECYCLE", "1800")))
    
    @property
    def url(self) -> str:
        """获取数据库连接 URL"""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @property
    def dsn(self) -> dict:
        """获取 psycopg2 连接参数"""
        return {
            "host": self.host,
            "port": self.port,
            "database": self.database,
            "user": self.user,
            "password": self.password,
        }


@dataclass
class RedisConfig:
    """Redis 缓存配置"""
    host: str = field(default_factory=lambda: os.getenv("REDIS_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("REDIS_PORT", "6379")))
    password: Optional[str] = field(default_factory=lambda: os.getenv("REDIS_PASSWORD"))
    db: int = field(default_factory=lambda: int(os.getenv("REDIS_DB", "0")))
    
    # 缓存过期时间（秒）
    default_expire: int = field(default_factory=lambda: int(os.getenv("REDIS_DEFAULT_EXPIRE", "3600")))
    gsd_cache_expire: int = field(default_factory=lambda: int(os.getenv("GSD_CACHE_EXPIRE", "3600")))
    
    @property
    def url(self) -> str:
        """获取 Redis 连接 URL"""
        password_part = f":{self.password}@" if self.password else ""
        return f"redis://{password_part}{self.host}:{self.port}/{self.db}"


@dataclass
class BackendConfig:
    """FastAPI 后端服务配置"""
    host: str = field(default_factory=lambda: os.getenv("BACKEND_HOST", "0.0.0.0"))
    port: int = field(default_factory=lambda: int(os.getenv("BACKEND_PORT", "8005")))
    workers: int = field(default_factory=lambda: int(os.getenv("BACKEND_WORKERS", "1")))
    reload: bool = field(default_factory=lambda: os.getenv("BACKEND_RELOAD", "true").lower() == "true")
    
    # CORS 配置
    cors_origins: List[str] = field(default_factory=lambda: [
        origin.strip() for origin in os.getenv(
            "CORS_ORIGINS", 
            "http://localhost:5173,http://localhost:5174,http://localhost:5175,http://localhost:5176"
        ).split(",")
    ])
    cors_allow_credentials: bool = field(default_factory=lambda: os.getenv("CORS_ALLOW_CREDENTIALS", "true").lower() == "true")


@dataclass
class OpenClawConfig:
    """OpenClaw Gateway 配置"""
    gateway_url: str = field(default_factory=lambda: os.getenv("OPENCLAW_GATEWAY_URL", "http://127.0.0.1:18789"))
    gateway_token: str = field(default_factory=lambda: os.getenv("OPENCLAW_GATEWAY_TOKEN", ""))
    gateway_ws: str = field(default_factory=lambda: os.getenv("OPENCLAW_GATEWAY_WS", "ws://127.0.0.1:18789"))
    
    @property
    def is_configured(self) -> bool:
        """检查 OpenClaw 是否正确配置"""
        return bool(self.gateway_token)


@dataclass
class GSDConfig:
    """GSD 智能问数配置"""
    api_version: str = field(default_factory=lambda: os.getenv("GSD_API_VERSION", "v25"))
    cache_enabled: bool = field(default_factory=lambda: os.getenv("GSD_CACHE_ENABLED", "true").lower() == "true")
    max_history: int = field(default_factory=lambda: int(os.getenv("GSD_MAX_HISTORY", "100")))
    quick_query_threshold: int = field(default_factory=lambda: int(os.getenv("GSD_QUICK_QUERY_THRESHOLD", "5")))


@dataclass
class LogConfig:
    """日志配置"""
    level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    format: str = field(default_factory=lambda: os.getenv("LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    file: str = field(default_factory=lambda: os.getenv("LOG_FILE", "logs/erp_agent.log"))


@dataclass
class SecurityConfig:
    """安全配置"""
    jwt_secret_key: str = field(default_factory=lambda: os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production"))
    jwt_algorithm: str = field(default_factory=lambda: os.getenv("JWT_ALGORITHM", "HS256"))
    jwt_access_token_expire_minutes: int = field(default_factory=lambda: int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30")))


@dataclass
class AppConfig:
    """应用全局配置"""
    environment: str = field(default_factory=lambda: os.getenv("ENVIRONMENT", "development"))
    debug: bool = field(default_factory=lambda: os.getenv("DEBUG", "true").lower() == "true")
    timezone: str = field(default_factory=lambda: os.getenv("TIMEZONE", "Asia/Shanghai"))


# ============================================================
# 全局配置实例
# ============================================================

# 数据库配置
neo4j_config = Neo4jConfig()
postgres_config = PostgresConfig()
redis_config = RedisConfig()

# 服务配置
backend_config = BackendConfig()
openclaw_config = OpenClawConfig()
gsd_config = GSDConfig()

# 其他配置
log_config = LogConfig()
security_config = SecurityConfig()
app_config = AppConfig()


# ============================================================
# 便捷函数
# ============================================================

def get_all_configs() -> dict:
    """获取所有配置（用于调试）"""
    return {
        "neo4j": {
            "uri": neo4j_config.uri,
            "user": neo4j_config.user,
            "password": "***" if neo4j_config.password else None,
            "database": neo4j_config.database,
            "timeout": neo4j_config.timeout,
            "is_configured": neo4j_config.is_configured,
        },
        "postgres": {
            "host": postgres_config.host,
            "port": postgres_config.port,
            "database": postgres_config.database,
            "user": postgres_config.user,
            "password": "***" if postgres_config.password else None,
            "url": postgres_config.url.split("@")[0] + "@***" if postgres_config.password else postgres_config.url,
        },
        "redis": {
            "host": redis_config.host,
            "port": redis_config.port,
            "db": redis_config.db,
            "expire": redis_config.default_expire,
        },
        "backend": {
            "host": backend_config.host,
            "port": backend_config.port,
            "reload": backend_config.reload,
            "cors_origins": backend_config.cors_origins,
        },
        "openclaw": {
            "gateway_url": openclaw_config.gateway_url,
            "gateway_token": "***" if openclaw_config.gateway_token else None,
            "is_configured": openclaw_config.is_configured,
        },
        "gsd": {
            "api_version": gsd_config.api_version,
            "cache_enabled": gsd_config.cache_enabled,
            "max_history": gsd_config.max_history,
        },
        "app": {
            "environment": app_config.environment,
            "debug": app_config.debug,
            "timezone": app_config.timezone,
        },
    }


def print_config_summary():
    """打印配置摘要（用于启动时检查）"""
    print("=" * 60)
    print("ERP Agent 配置摘要")
    print("=" * 60)
    
    configs = get_all_configs()
    
    # Neo4j
    neo4j = configs["neo4j"]
    print(f"\n[Neo4j]")
    print(f"  URI: {neo4j['uri']}")
    print(f"  用户：{neo4j['user']}")
    print(f"  密码：{'已配置' if neo4j['password'] else '未配置 ⚠️'}")
    print(f"  超时：{neo4j['timeout']}s")
    
    # PostgreSQL
    pg = configs["postgres"]
    print(f"\n[PostgreSQL]")
    print(f"  主机：{pg['host']}:{pg['port']}")
    print(f"  数据库：{pg['database']}")
    print(f"  用户：{pg['user']}")
    print(f"  密码：{'已配置' if pg['password'] else '未配置 ⚠️'}")
    
    # Redis
    redis = configs["redis"]
    print(f"\n[Redis]")
    print(f"  主机：{redis['host']}:{redis['port']}")
    print(f"  数据库：{redis['db']}")
    print(f"  过期时间：{redis['expire']}s")
    
    # Backend
    backend = configs["backend"]
    print(f"\n[Backend Service]")
    print(f"  地址：{backend['host']}:{backend['port']}")
    print(f"  热重载：{'开启' if backend['reload'] else '关闭'}")
    print(f"  CORS 来源：{len(backend['cors_origins'])} 个")
    
    # OpenClaw
    oc = configs["openclaw"]
    print(f"\n[OpenClaw Gateway]")
    print(f"  URL: {oc['gateway_url']}")
    print(f"  Token: {'已配置' if oc['is_configured'] else '未配置 ⚠️'}")
    
    # GSD
    gsd = configs["gsd"]
    print(f"\n[GSD 智能问数]")
    print(f"  API 版本：{gsd['api_version']}")
    print(f"  缓存：{'开启' if gsd['cache_enabled'] else '关闭'}")
    print(f"  历史数量：{gsd['max_history']}")
    
    # App
    app = configs["app"]
    print(f"\n[Application]")
    print(f"  环境：{app['environment']}")
    print(f"  调试：{'开启' if app['debug'] else '关闭'}")
    print(f"  时区：{app['timezone']}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    # 测试配置加载
    print_config_summary()
