"""
core/config.py — 全局配置中心
从 config.json 文件中加载所有基础设施参数。
⚠️  禁止在此处编写任何业务逻辑。
"""
import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, field_validator


def _resolve_config_path() -> Path:
    """解析 config.json 路径：优先使用 CONFIG_PATH 环境变量，否则使用项目根目录。"""
    env_path = os.environ.get("CONFIG_PATH")
    if env_path:
        return Path(env_path).resolve()
    # config.py 位于 app/core/，项目根目录在其上两级
    return Path(__file__).resolve().parents[2] / "config.json"


def _coerce_env_value(key: str, env_val: str) -> object:
    """
    将环境变量字符串转为 Settings 字段对应的正确类型。
    处理 bool / int / float 的常见转换，其余保持原字符串。
    """
    # bool 转换：Pydantic 不直接读字符串，需手动映射
    if key in ("DEBUG", "MAP_USE_SQLITE"):
        return env_val.lower() in ("true", "1", "yes")
    # int 转换
    if key in ("DB_PORT", "DB_POOL_SIZE", "DB_MAX_OVERFLOW", "DB_POOL_RECYCLE",
               "REDIS_PORT", "REDIS_DB", "REDIS_MAX_CONNECTIONS",
               "ACCESS_TOKEN_EXPIRE_MINUTES", "EXTERNAL_HTTP_RETRIES"):
        return int(env_val)
    # float 转换
    if key == "EXTERNAL_HTTP_TIMEOUT":
        return float(env_val)
    return env_val


def _load_config() -> dict:
    config_path = _resolve_config_path()
    if not config_path.exists():
        raise FileNotFoundError(
            f"config.json not found at {config_path}. "
            f"Set CONFIG_PATH env var to override, or place config.json in the project root."
        )
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    # 环境变量可覆盖 config.json 同名字段
    # 用于 PaaS 平台部署时：同一份 config.json + 平台环境变量区分环境
    for key in Settings.model_fields.keys():
        if env_val := os.environ.get(key):
            data[key] = _coerce_env_value(key, env_val)

    return data


class Settings(BaseModel):
    # ── 服务基础 ─────────────────────────────────────────────────────────────
    APP_ENV: Literal["development", "staging", "production"] = "development"
    APP_NAME: str = "MAP Backend"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = Field(default=False)

    @field_validator("SECRET_KEY")
    @classmethod
    def check_secret_key(cls, v: str, info) -> str:
        app_env = info.data.get("APP_ENV", "development")
        if app_env == "production" and v == "change-me-in-production":
            raise ValueError("SECRET_KEY must be set to a strong random value in production")
        return v

    # ── 数据库 ────────────────────────────────────────────────────────────────
    # 默认连 TDSQL for MySQL 8（端口 5400）；本地无 TDSQL 时可设 MAP_USE_SQLITE=true
    MAP_USE_SQLITE: bool = Field(
        default=False,
        description="为 true 时使用本地 SQLite，不访问 DB_HOST（适合仅跑前端联调）",
    )
    MAP_SQLITE_PATH: str = Field(
        default="./map_local.sqlite",
        description="SQLite 文件路径，相对 uvicorn 启动时的当前工作目录（建议在 backend 目录启动）",
    )
    # TDSQL 默认端口 5400（标准 MySQL 为 3306）
    DB_HOST: str = "127.0.0.1"
    DB_PORT: int = 5400
    DB_USER: str = "map_user"
    DB_PASSWORD: str = ""
    DB_NAME: str = "map_db"
    DB_CHARSET: str = "utf8mb4"
    # 连接池（TDSQL / MySQL 共用）
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_RECYCLE: int = 3600  # seconds

    @property
    def DATABASE_URL(self) -> str:
        """异步驱动 URL，供 AsyncEngine 使用。"""
        if self.MAP_USE_SQLITE:
            p = Path(self.MAP_SQLITE_PATH)
            abs_path = p.resolve() if not p.is_absolute() else p
            return f"sqlite+aiosqlite:///{abs_path.as_posix()}"
        return (
            f"mysql+aiomysql://{self.DB_USER}:{self.DB_PASSWORD}"
            f"@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
            f"?charset={self.DB_CHARSET}"
        )

    # ── Redis ─────────────────────────────────────────────────────────────────
    REDIS_HOST: str = "127.0.0.1"
    REDIS_PORT: int = 6379
    REDIS_PASSWORD: str = ""
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 50

    @property
    def REDIS_URL(self) -> str:
        auth = f":{self.REDIS_PASSWORD}@" if self.REDIS_PASSWORD else ""
        return f"redis://{auth}{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # ── RocketMQ ──────────────────────────────────────────────────────────────
    ROCKETMQ_NAME_SERVER: str = "127.0.0.1:9876"
    ROCKETMQ_PRODUCER_GROUP: str = "MAP_PRODUCER_GROUP"
    ROCKETMQ_CONSUMER_GROUP: str = "MAP_CONSUMER_GROUP"
    ROCKETMQ_TOPIC: str = "MAP_EVENTS"

    # ── 安全 ──────────────────────────────────────────────────────────────────
    SECRET_KEY: str = Field(
        default="change-me-in-production",
        description="JWT / 签名密钥，生产环境必须替换",
    )
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 小时

    # ── 外部系统超时 (seconds) ────────────────────────────────────────────────
    EXTERNAL_HTTP_TIMEOUT: float = 10.0
    EXTERNAL_HTTP_RETRIES: int = 3

    # ── SSO / 统一门户 ────────────────────────────────────────────────────────
    SSO_VALIDATE_URL: str = Field(
        default="http://pawm-pfp-service-gateway.dev.pab.com.cn/wmuc/loginServer/loginValidateToken",
        description="门户 token 校验远程接口地址（后端调用）",
    )
    SSO_LOGIN_URL: str = Field(
        default="http://wm.dev.paic.com.cn/lckj/pawm-uc/account_login.html",
        description=(
            "门户登录页地址（浏览器跳转）。dev=wm.dev.paic / fat=wm.stg.paic / prd=wm.paic。"
            "前端在用户未登录时把浏览器跳到 `${SSO_LOGIN_URL}?url=<我方根 URL>`。"
        ),
    )
    SSO_LOGIN_REDIRECT_URL: str = Field(
        default="http://localhost:5173",
        description="SSO 认证成功后浏览器最终落地的前端 URL",
    )

    # ── CORS ─────────────────────────────────────────────────────────────────
    CORS_ORIGINS: str = Field(
        default="*",
        description="允许的 CORS 来源，逗号分隔多个域名，* 表示全开放（生产环境应明确指定）",
    )

    @property
    def cors_origins_list(self) -> list[str] | None:
        """将 CORS_ORIGINS 字符串解析为列表。* 返回 None（允许所有）。"""
        if self.CORS_ORIGINS.strip() == "*":
            return None
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    # ── 外部系统 URL（未配置时使用 Mock 模式） ─────────────────────────────
    PORTFOLIO_SYS_URL: str = Field(
        default="",
        description="组合系统 API 地址，未配置时自动使用 Mock 适配器",
    )
    RISK_SYS_URL: str = Field(
        default="",
        description="风控系统 API 地址，未配置时自动使用 Mock 适配器",
    )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """单例工厂，FastAPI Depends 注入时使用。"""
    return Settings(**_load_config())


# 模块级快捷访问（非 DI 场景下导入使用）
settings: Settings = get_settings()
