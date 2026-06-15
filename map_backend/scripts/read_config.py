#!/usr/bin/env python3
"""读取 config.json，输出为 shell 可 source 的 KEY=VALUE 格式。
环境变量优先：若某 key 已在环境中设置（非空），则跳过。
"""
import json, os, sys


def main() -> int:
    config_path = os.environ.get("CONFIG_PATH", "")
    if not config_path or not os.path.isfile(config_path):
        print("ERROR: config.json not found at %s" % config_path, file=sys.stderr)
        return 1

    with open(config_path, "r", encoding="utf-8") as f:
        d = json.load(f)

    keys = [
        "DB_HOST", "DB_PORT", "DB_USER", "DB_PASSWORD", "DB_NAME", "DB_CHARSET",
        "MAP_USE_SQLITE", "MAP_SQLITE_PATH",
    ]
    for k in keys:
        env_val = os.environ.get(k, "").strip()
        if env_val:
            continue
        v = d.get(k, "")
        # 单引号包裹 value，内部单引号做 shell 转义
        v_str = str(v).replace("'", "'\"'\"'")
        sys.stdout.write("%s='%s'\n" % (k, v_str))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
