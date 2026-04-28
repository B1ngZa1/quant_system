"""应用配置模块"""

import json
from functools import lru_cache
from pathlib import Path
from typing import List, Optional

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings
from typing_extensions import Self

# 禁止在生产环境使用的占位密钥/口令（与 .env.example 中示例一致）
_FORBIDDEN_SECRET_KEYS = frozenset(
    {
        "",
        "your-super-secret-key-change-in-production",
        "dev-secret-key-change-me",
    }
)
_FORBIDDEN_DB_PASSWORDS = frozenset(
    {
        "",
        "quant_password",
    }
)


class Settings(BaseSettings):
    """应用配置类"""

    # 应用基础配置
    APP_NAME: str = "Quant Trading System"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"

    # API 配置
    API_PREFIX: str = "/api"
    API_V1_STR: str = "/api/v1"

    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # 安全配置（开发环境请在 .env 中设置；生产必须通过环境变量注入强随机密钥）
    SECRET_KEY: str = ""
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    ALGORITHM: str = "HS256"

    # CORS 配置
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: List[str] = ["*"]
    CORS_ALLOW_HEADERS: List[str] = ["*"]

    # 数据库配置 - PostgreSQL / TimescaleDB
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "quant_user"
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = "quant_db"
    POSTGRES_POOL_SIZE: int = 20
    POSTGRES_MAX_OVERFLOW: int = 10

    # 数据库配置 - MySQL (如果 DATABASE_TYPE=mysql 时使用)
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "quant_user"
    MYSQL_PASSWORD: str = ""
    MYSQL_DATABASE: str = "quant_db"
    MYSQL_POOL_SIZE: int = 20
    MYSQL_MAX_OVERFLOW: int = 10

    # 数据库配置 - SQLite (备用)
    SQLITE_URL: str = "sqlite+aiosqlite:///./data/quant.db"
    # 数据库类型：postgres/mysql/sqlite
    DATABASE_TYPE: str = "postgres"

    # Redis 配置
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    REDIS_POOL_SIZE: int = 10

    # 缓存配置
    CACHE_DEFAULT_TIMEOUT: int = 300  # 5分钟
    CACHE_STOCK_DATA_TIMEOUT: int = 60  # 1分钟
    CACHE_REALTIME_TIMEOUT: int = 10  # 10秒

    # DeepSeek AI 配置
    DEEPSEEK_API_KEY: Optional[str] = None
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-chat"

    # Tushare 配置
    TUSHARE_TOKEN: Optional[str] = None

    # 本地数据集目录（CSV：行情快照 market_snapshot.csv；K 线：{6位代码}.csv 或 ohlcv/{代码}.csv）
    # 留空则使用 backend/data/local_datasets（相对项目 backend 根目录）
    LOCAL_DATA_DIR: Optional[str] = None

    # A 股「按交易日全市场横截面」CSV 根目录（形如 前复权/2001/2001-12-04.csv）。留空则使用仓库根目录 daily_data/前复权，其次 local_datasets/a_share_daily_adj
    A_SHARE_DAILY_PANEL_DIR: Optional[str] = None

    # 聚合行情是否在 AKShare/备份库不可用后读取 market_snapshot.csv（未搭建本地快照时建议 False）
    USE_LOCAL_CSV_QUOTES_FALLBACK: bool = False

    # 行情列表：优先读本地库 stock_realtime；数据早于该分钟数则改拉 AKShare（本地为主 + 联网刷新）
    DATA_QUOTES_DB_MAX_AGE_MINUTES: int = 360

    # 聚合行情：在「本地库过期/不可用」时，优先读仓库 daily_data/前复权（或 A_SHARE_DAILY_PANEL_DIR）横截面 CSV，再尝试 AKShare（显著减少网络等待）
    QUOTES_PREFER_LOCAL_DAILY_PANEL: bool = True

    # 每日定时同步（A 股增量 K 线 + 实时表写入 DB）
    ENABLE_DAILY_MARKET_SYNC: bool = True
    # 本地时区（如 Asia/Shanghai）下每日触发的小时与分钟
    DAILY_MARKET_SYNC_HOUR: int = 18
    DAILY_MARKET_SYNC_MINUTE: int = 30
    # 每日增量最多处理股票数；0 表示不限制（全市场较慢）
    DAILY_INCREMENTAL_SYMBOL_LIMIT: int = 0
    # 增量同步回溯交易日数（含节假日冗余）
    DAILY_INCREMENTAL_LOOKBACK_DAYS: int = 15

    # 交易配置
    TRADING_COMMISSION_RATE: float = 0.0003  # 佣金率 0.03%
    TRADING_MIN_COMMISSION: float = 5.0  # 最低佣金
    TRADING_SLIPPAGE: float = 0.001  # 滑点 0.1%

    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name} | {message}"

    # 审计日志配置
    AUDIT_LOG_RETENTION_DAYS: int = 90

    # 限流配置
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_GLOBAL_MAX_REQUESTS: int = 300
    RATE_LIMIT_AUTH_MAX_REQUESTS: int = 20

    # 回测与策略配置
    ALLOW_CUSTOM_STRATEGY_CODE_EXEC: bool = False

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):
        if v is None:
            return v
        if isinstance(v, list):
            return v
        if isinstance(v, str):
            text = v.strip()
            if not text:
                return []
            if text.startswith("["):
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, list):
                        return [str(x).strip() for x in parsed if str(x).strip()]
                except Exception:
                    return [text]
            parts = [p.strip() for p in text.split(",")]
            return [p for p in parts if p]
        return v

    @model_validator(mode="after")
    def validate_secrets_and_prod_rules(self) -> Self:
        env = (self.ENVIRONMENT or "").lower()
        if env in ("production", "staging"):
            if self.SECRET_KEY in _FORBIDDEN_SECRET_KEYS or len(self.SECRET_KEY) < 32:
                raise ValueError(
                    "生产/预发布环境必须设置长度不少于 32 的 SECRET_KEY（环境变量），"
                    "且不得使用占位符"
                )
            if self.POSTGRES_PASSWORD in _FORBIDDEN_DB_PASSWORDS:
                raise ValueError(
                    "生产/预发布环境必须设置 POSTGRES_PASSWORD（环境变量），且不得使用默认占位口令"
                )
            origins = [x.strip() for x in (self.CORS_ORIGINS or []) if x and str(x).strip()]
            if not origins:
                raise ValueError("生产/预发布环境必须设置 CORS_ORIGINS（环境变量）")
            if any(o == "*" for o in origins):
                raise ValueError("生产/预发布环境 CORS_ORIGINS 不允许为 *")
            if any(("localhost" in o) or ("127.0.0.1" in o) for o in origins):
                raise ValueError("生产/预发布环境 CORS_ORIGINS 不允许包含 localhost/127.0.0.1")
            object.__setattr__(self, "ALLOW_CUSTOM_STRATEGY_CODE_EXEC", False)
        else:
            # 开发/测试：未配置时使用非安全的本地默认值，便于开箱运行
            if not self.SECRET_KEY or self.SECRET_KEY in _FORBIDDEN_SECRET_KEYS:
                object.__setattr__(
                    self,
                    "SECRET_KEY",
                    "dev-only-insecure-secret-key-change-in-env-file",
                )
            if not self.POSTGRES_PASSWORD:
                object.__setattr__(self, "POSTGRES_PASSWORD", "quant_password")
        return self

    @property
    def postgres_url(self) -> str:
        """生成 PostgreSQL 数据库 URL"""
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def sync_postgres_url(self) -> str:
        """生成同步 PostgreSQL 数据库 URL (Alembic)"""
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def mysql_url(self) -> str:
        """生成 MySQL 数据库 URL"""
        return (
            f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    @property
    def sync_mysql_url(self) -> str:
        """生成同步 MySQL 数据库 URL"""
        return (
            f"mysql+pymysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}"
            f"@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
        )

    @property
    def sync_sqlite_url(self) -> str:
        """生成同步 SQLite 数据库 URL（供 Alembic 使用）"""
        return self.SQLITE_URL.replace("+aiosqlite", "")

    @property
    def local_data_path(self) -> Path:
        """本地行情/K 线 CSV 根目录。"""
        if self.LOCAL_DATA_DIR:
            return Path(self.LOCAL_DATA_DIR).expanduser().resolve()
        # backend/app/core/config.py -> parents[2] == backend
        return Path(__file__).resolve().parents[2] / "data" / "local_datasets"

    @property
    def redis_url(self) -> str:
        """生成 Redis URL"""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"


@lru_cache()
def get_settings() -> Settings:
    """获取配置单例"""
    return Settings()


settings = get_settings()
