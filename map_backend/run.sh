#!/usr/bin/env bash
# =============================================================================
# run.sh — MAP Backend 生产启动脚本
#
# 用途：公司内网 PaaS 流水线入口，一键完成：
#   1. 安装依赖（走内部 PyPI 镜像）
#   2. 检查并创建数据库（幂等：已建则跳过）
#   3. 首次建表（幂等：已建表则无副作用）
#   4. 启动 Uvicorn
#
# 环境变量：
#   CONFIG_PATH      — config.json 路径（可选，默认项目根目录）
#   DB_HOST/PORT/USER/PASSWORD/NAME  — 数据库连接参数
#   INTERNAL_PYPI    — 内部 PyPI 镜像地址（可选）
#   WORKERS          — Uvicorn worker 数量（默认 4）
#   PORT             — 监听端口（默认 8000）
# =============================================================================
set -euo pipefail

# ── 颜色输出 ─────────────────────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info()  { echo -e "${GREEN}[INFO]${NC}  $*"; }
log_warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
log_error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ── 变量读取（环境变量优先，其次 config.json）────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# config.json 路径
CONFIG_PATH="${CONFIG_PATH:-${SCRIPT_DIR}/config.json}"
if [[ ! -f "${CONFIG_PATH}" ]]; then
    log_error "config.json not found at ${CONFIG_PATH}"
    log_error "Set CONFIG_PATH env var to override."
    exit 1
fi

# 导出 CONFIG_PATH，调用 Python 脚本输出 KEY=VALUE，source 到当前 shell
CONFIG_SCRIPT=$(mktemp /tmp/map_read_config.XXXXXX.sh)
trap "rm -f ${CONFIG_SCRIPT}" EXIT

export CONFIG_PATH
python3 "${SCRIPT_DIR}/scripts/read_config.py" > "${CONFIG_SCRIPT}"

log_info "Loading config from ${CONFIG_PATH} ..."
source "${CONFIG_SCRIPT}"

# 给部分字段兜底默认值（不影响 DB 必填校验）
MAP_USE_SQLITE="${MAP_USE_SQLITE:-false}"
MAP_SQLITE_PATH="${MAP_SQLITE_PATH:-./map_local.sqlite}"
DB_CHARSET="${DB_CHARSET:-utf8mb4}"
DB_PORT="${DB_PORT:-3306}"

# 校验必填字段（非 SQLite 模式下必须完整）
if [[ "${MAP_USE_SQLITE}" != "true" ]]; then
    for key in DB_HOST DB_USER DB_PASSWORD DB_NAME; do
        val="${!key}"
        if [[ -z "${val}" ]]; then
            log_error "${key} is empty — set it via env var or config.json before running."
            exit 1
        fi
    done
    log_info "DB config validated: ${DB_USER}@${DB_HOST}:${DB_PORT}/${DB_NAME}"
else
    log_info "Using SQLite: ${MAP_SQLITE_PATH}"
fi

# 其他变量
INTERNAL_PYPI="${INTERNAL_PYPI:-}"
WORKERS="${WORKERS:-4}"
PORT="${PORT:-8000}"

log_info "CONFIG_PATH   = ${CONFIG_PATH}"
log_info "DB_HOST       = ${DB_HOST}"
log_info "DB_PORT       = ${DB_PORT}"
log_info "DB_NAME       = ${DB_NAME}"
log_info "MAP_USE_SQLITE= ${MAP_USE_SQLITE}"
log_info "WORKERS       = ${WORKERS}"
log_info "PORT          = ${PORT}"

# ── 1. 安装依赖 ───────────────────────────────────────────────────────────────
log_info "Installing dependencies ..."
if [[ -n "${INTERNAL_PYPI}" ]]; then
    pip install -r "${SCRIPT_DIR}/requirements.txt" -i "${INTERNAL_PYPI}" --quiet
else
    pip install -r "${SCRIPT_DIR}/requirements.txt" --quiet
fi
log_info "Dependencies installed."

# ── 2. 数据库初始化（仅 MySQL 模式）───────────────────────────────────────────
if [[ "${MAP_USE_SQLITE}" == "true" ]]; then
    log_warn "MAP_USE_SQLITE=true, skipping MySQL database creation."
else
    export DB_HOST DB_PORT DB_USER DB_PASSWORD DB_NAME DB_CHARSET
    if ! python3 "${SCRIPT_DIR}/scripts/init_db.py"; then
        log_error "Database initialization failed. Aborting."
        exit 1
    fi
fi

# ── 3. 启动 Uvicorn ──────────────────────────────────────────────────────────
log_info "Starting Uvicorn on 0.0.0.0:${PORT} with ${WORKERS} workers ..."
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port "${PORT}" \
    --workers "${WORKERS}" \
    --proxy-headers \
    --forwarded-allow-ips='*'
