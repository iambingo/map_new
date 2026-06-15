#!/usr/bin/env python3
"""数据库初始化脚本：检查库是否存在 → 不存在则建库 → 建表。
通过环境变量读取数据库连接参数，兼容 PaaS 平台注入。

用法：
    export DB_HOST=... DB_PORT=3306 DB_USER=... DB_PASSWORD=... DB_NAME=...
    python3 scripts/init_db.py          # 检查 + 建库 + 建表
    python3 scripts/init_db.py --check  # 仅检查数据库是否存在
"""
import asyncio
import os
import sys


def get_env(key: str, default: str = "") -> str:
    return os.environ.get(key, default)


def check_db_exists() -> bool:
    """检查数据库是否存在。"""
    import pymysql

    host = get_env("DB_HOST")
    port = int(get_env("DB_PORT", "3306"))
    user = get_env("DB_USER")
    password = get_env("DB_PASSWORD")
    db_name = get_env("DB_NAME")
    charset = get_env("DB_CHARSET", "utf8mb4")

    conn = pymysql.connect(
        host=host, port=port, user=user, password=password, charset=charset
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT SCHEMA_NAME FROM INFORMATION_SCHEMA.SCHEMATA WHERE SCHEMA_NAME = %s",
                (db_name,),
            )
            exists = cur.fetchone()
            return exists is not None
    finally:
        conn.close()


def create_db() -> None:
    """创建数据库（IF NOT EXISTS）。"""
    import pymysql

    host = get_env("DB_HOST")
    port = int(get_env("DB_PORT", "3306"))
    user = get_env("DB_USER")
    password = get_env("DB_PASSWORD")
    db_name = get_env("DB_NAME")
    charset = get_env("DB_CHARSET", "utf8mb4")

    conn = pymysql.connect(
        host=host, port=port, user=user, password=password, charset=charset
    )
    try:
        with conn.cursor() as cur:
            cur.execute(
                "CREATE DATABASE IF NOT EXISTS `%s` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci" % db_name
            )
        conn.commit()
    finally:
        conn.close()


async def create_tables() -> None:
    """通过 SQLAlchemy 模型创建所有表（幂等）。"""
    # 确保项目根目录在 sys.path 中
    script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if script_dir not in sys.path:
        sys.path.insert(0, script_dir)

    from app.core.db_tdsql import _ensure_engine_and_factory
    from app.core.orm_base import Base

    # 导入所有模型模块（副作用：注册到 Base.metadata）
    import app.modules.committee.models           # noqa: F401
    import app.modules.committee.mixed_models     # noqa: F401
    import app.modules.orchestrator.models        # noqa: F401
    import app.modules.asset_allocation.models    # noqa: F401
    import app.modules.auth.models                # noqa: F401

    factory = _ensure_engine_and_factory()
    engine = factory.kw["bind"]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

    tables = sorted(Base.metadata.tables.keys())
    print(f"OK: {len(tables)} tables ensured: {', '.join(tables)}")


def main() -> int:
    db_name = get_env("DB_NAME")
    host = get_env("DB_HOST")
    port = get_env("DB_PORT", "3306")

    check_only = "--check" in sys.argv

    # ── 1. 检查数据库是否存在 ──
    print(f"Checking if database '{db_name}' exists on {host}:{port} ...")
    try:
        exists = check_db_exists()
    except Exception as e:
        print(f"ERROR: Failed to check database: {e}", file=sys.stderr)
        if check_only:
            return 1
        # 检查失败，尝试直接创建
        print("Attempting to create database anyway ...")
        try:
            create_db()
            print(f"Database '{db_name}' created.")
        except Exception as e2:
            print(f"FATAL: Cannot create database: {e2}", file=sys.stderr)
            return 1
        if check_only:
            return 0
        # 继续建表
    else:
        if exists:
            print(f"Database '{db_name}' already exists, skipping creation.")
        else:
            if check_only:
                print(f"Database '{db_name}' does NOT exist.")
                return 1
            print(f"Database '{db_name}' does not exist. Creating ...")
            create_db()
            print(f"Database '{db_name}' created successfully.")

    if check_only:
        return 0

    # ── 2. 建表 ──
    print("Creating tables from ORM models (idempotent) ...")
    asyncio.run(create_tables())
    print("Tables initialized.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
