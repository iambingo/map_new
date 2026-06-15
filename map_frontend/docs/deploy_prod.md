# MAP 后端 · 公司内网部署上线文档

> 适用环境：公司内网（无外网）｜目标：FastAPI + TDSQL for MySQL 8 + Redis + RocketMQ + 门户 SSO
> 本文件聚焦"上线"，本地开发请看 `deploy.md`。

---

## 1. 总体架构与依赖资源

```
                  ┌────────────────────────┐
浏览器 ──────────►│  公司统一门户 / SSO   │
                  └──────────┬─────────────┘
                             │ 302 ?ssoTokenId=xxx
                             ▼
                  ┌────────────────────────┐         ┌──────────────────┐
                  │  MAP Backend (FastAPI) │◄───────►│  TDSQL for MySQL │
                  │  Uvicorn :8000         │         │  :5400           │
                  └──┬───────┬───────┬─────┘         └──────────────────┘
                     │       │       │
                     │       │       └──────► Redis :6379（缓存/SSE 总线）
                     │       │
                     │       └────────────────► RocketMQ NameServer :9876
                     │
                     └─► 组合系统 / 风控系统 / 门户校验接口（HTTP）
```

**应用进程清单**（同一份代码，按需起多份）：

| 进程 | 启动命令 | 说明 |
|------|----------|------|
| Web API | `uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4` | 提供 HTTP / SSE，包含 MQ 生产者 |
| MQ 消费者 | 同上（lifespan 内自动启动） | 由 `consumer_worker` 守护，无需独立进程 |

> 如果计划独立部署消费者（推荐生产模式），需要将 `app/modules/consumers/worker.py` 改造为独立 entrypoint；当前实现已经在 `lifespan` 里启动，单 Web 实例即可工作，但**多实例水平扩展时只能有 1 个 Web 实例承担消费角色**，建议先用单实例上线，水平扩容再拆分。

---

## 2. 内网部署步骤

### 2.1 代码侧准备

**部署模式**：公司 PaaS 平台已建好容器运行时，开发只交付**代码**。流程是 push 到 GitLab 测试分支 → 平台 UI 点 "发布" → 平台拉代码、装依赖、起进程、挂域名。

代码侧（仓库根目录）必须就位的文件：

| 文件 | 状态 | 作用 |
|------|------|------|
| `requirements.txt` | ✅ 已有 | 平台执行 `pip install -r requirements.txt` 装依赖（走平台内置的内部 PyPI 镜像） |
| `app/` | ✅ 已有 | FastAPI 应用包，入口 `app.main:app` |
| `Procfile` 或平台启动配置 | ⚠️ 见 2.4 | 声明启动命令；具体格式由平台定 |
| `.gitignore` | ✅ 已有 | 已排除 `map_wheels/`、`.claude/`、`venv/` |
| `.dockerignore` | ✅ 已有 | 防御性配置：若平台构建走 Docker 体系，这份排除清单会被识别，避免把 `.venv/`、`__pycache__/`、`.claude/`、本地 SQLite、`deploy_prod.md` 等本地开发噪声打进镜像 |

**不需要**：`Dockerfile`、K8s YAML、wheel 离线包——平台都管。

#### 2.1.1 需要向平台部确认的 6 件事

| # | 项 | 写进部署配置时填什么 |
|---|---|---|
| 1 | 运行时 Python 版本 | 必须 **3.10**（与 `requirements.txt` 中 C 扩展的 wheel ABI 匹配）。若平台只提供 3.11/3.12，需重新跑兼容性测试 |
| 2 | 内部 PyPI 镜像地址 | 平台默认应已配好；确认能解析 `pydantic-core`、`cryptography`、`bcrypt`、`uvloop` 等 C 扩展 |
| 3 | 启动命令 | 见 2.4 |
| 4 | 监听端口 | `8000`（FastAPI 默认 uvicorn 端口；可通过启动命令改） |
| 5 | 健康检查路径 | `GET /health`，期望 200 + `{"status":"ok",...}` |
| 6 | 环境变量 / 配置文件挂载方式 | 见 2.3 |

#### 2.1.2 RocketMQ SDK 单独说明

`rocketmq-client-python` 只有 sdist 且 import-time 要 `dlopen` 系统库 `librocketmq.so`。**首期建议直接跳过**——`requirements.txt` 里这一行已经注释掉，代码会自动降级为 stub 模式（日志 `RocketMQ consumer worker started (sdk=False)`），异步指令落 `pending_commands` 表标 PENDING，不阻断启动。

要启用时需要平台部协助：
1. 在基础镜像里装好 `librocketmq` 系统库（提工单）
2. 把内部 PyPI 镜像同步 `rocketmq-client-python==2.0.0` 的 sdist
3. 取消 `requirements.txt` 中该行的注释，重新发布

### 2.2 数据库初始化

数据库由 DBA 在 TDSQL 集群上创建：

```sql
CREATE DATABASE mapdb DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'map_app'@'%' IDENTIFIED BY '<由 DBA 生成的强密码>';
GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, DROP, INDEX, ALTER, REFERENCES ON mapdb.* TO 'map_app'@'%';
FLUSH PRIVILEGES;
```

> 业务表通过 SQLAlchemy `metadata.create_all` 自动建立，无需手工建表。如 DBA 不允许应用账号有 DDL 权限，请先用 DBA 账号执行下方 Python 脚本建表，再回收 `CREATE/DROP/ALTER` 权限。

首次建表（测试环境首次发布成功后，在平台 Web Terminal 进入运行中的容器执行一次；生产环境同样在首次发布后执行一次）：
```bash
cd /opt/map_backend
export CONFIG_PATH=/etc/map/config.json
python - <<'PY'
import asyncio
from app.core.db_tdsql import _ensure_engine_and_factory
from app.core.orm_base import Base
import app.modules.committee.models           # noqa
import app.modules.committee.mixed_models     # noqa
import app.modules.orchestrator.models        # noqa
import app.modules.asset_allocation.models    # noqa
import app.modules.auth.models                # noqa

async def main():
    factory = _ensure_engine_and_factory()
    engine = factory.kw["bind"]
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    await engine.dispose()

asyncio.run(main())
print("OK: tables created.")
PY
```

涉及的表（合计 8 张，均无物理外键）：`map_users`、`ic_meetings`、`ic_vote_records`、`ic_resolutions`、`ic_chair_resolutions`、`mixed_submissions`、`pending_commands`、`saa_drafts`（具体以模型 `__tablename__` 为准）。

### 2.3 运行时配置注入

`config.json` **绝不进 Git**。在平台的"环境变量 / 配置中心"页面分两类录入，**全部走环境变量**（代码里 `app/core/config.py` 已支持环境变量覆盖 `config.json` 同名字段）：

| 分类 | 内容 | 平台 UI 填法 |
|------|------|--------------|
| 非敏感（普通环境变量） | `APP_ENV=production`、`DEBUG=false`、`DB_HOST`、`DB_PORT`、`DB_NAME`、`DB_USER`、`DB_CHARSET`、`REDIS_HOST`、`REDIS_PORT`、`SSO_VALIDATE_URL`、`PORTFOLIO_SYS_URL`、`RISK_SYS_URL` 等 | "环境变量" 直接键值录入 |
| 敏感（凭据） | `DB_PASSWORD`、`REDIS_PASSWORD`、`SECRET_KEY`、`PORTAL_CLIENT_SECRET` | 平台一般有"密钥/Secret 管理"或"加密配置"开关，把这几项勾上加密；**不要直接写进普通环境变量框** |

**两种等效注入方式**（看平台支持哪个，二选一即可）：

1. **纯环境变量**：所有字段都通过平台 UI 录入环境变量，**不需要** `config.json` 文件。代码 `_load_config()` 会在缺文件时跳过加载、纯走环境变量。
2. **配置文件 + 环境变量**：平台支持"配置文件挂载"时，把非敏感字段写成 `config.json` 内容贴进去，平台挂到容器内某路径，再设置环境变量 `CONFIG_PATH=<挂载路径>/config.json`；敏感字段单独走加密环境变量。

> 完整字段清单见本文档 **第 5 节 · 配置表**。先按方式 1 录入最省事，缺哪个字段补哪个。



### 2.4 启动命令

在平台的"启动命令 / Procfile / Entrypoint"配置项里填：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers --forwarded-allow-ips=*
```

逐项说明：

| 参数 | 必须 | 原因 |
|------|------|------|
| `--host 0.0.0.0` | ✅ | 容器内必须监听全部网卡，否则平台健康检查打不进来 |
| `--port 8000` | ⚠️ | 与平台 UI 里填的"监听端口"一致即可；如果平台强制要 8080，把这里和端口字段一起改 |
| `--workers 4` | 建议 | 单 Pod 起 4 个 worker 进程；按平台分配的 CPU 配额调（一般 worker 数 ≈ CPU 核数） |
| `--proxy-headers --forwarded-allow-ips=*` | ✅ | 平台 Ingress 前置代理，必须信任 `X-Forwarded-*` 头，否则 `request.client.host` 是平台代理 IP、`scheme` 永远是 http，SSO 回调 Cookie 的 Secure/HttpOnly 判断会错 |

> **关于 `--workers` 与 RocketMQ 消费者**
> 当前代码 `app/core/rocketmq_client.py` 把消费者放在 FastAPI `lifespan` 启动。`--workers > 1` 会让每个 worker 都起一份消费者，同一 ConsumerGroup 下**重复消费**（见第 10 节风险项 #2）。
> - 首期 RocketMQ 走 stub 模式 → `--workers 4` 没问题（stub 不消费真实消息）
> - 启用 RocketMQ 后 → 要么 `--workers 1`，要么先做消费者拆分改造

### 2.5 域名与对外路径

域名（如 `map.intranet.company.com`）、TLS 证书、Ingress 路由全部由平台分配/管理。你需要在平台的"域名 / 路由"配置页：

| 配置项 | 取值 | 备注 |
|--------|------|------|
| 对外域名 | 由平台分配，跟门户对接方报这个值即可 | 通常形如 `<app-name>.intranet.company.com` |
| 入口路径 | `/`（整站后端服务） | 不需要按 path 拆 |
| 后端端口 | `8000`（与 2.4 一致） | |
| 协议 | HTTPS（平台终止 TLS） | |

#### 必须找平台部协助打开/确认的 3 个特殊点

| 场景 | 涉及路径 | 配置项 |
|------|---------|--------|
| SSE 长连接 | `/api/v1/messages/events/stream` | **关闭代理缓冲 + 读超时拉长到 ≥ 1 小时**。平台 Ingress 是 Nginx 体系：要 `proxy_buffering off; proxy_read_timeout 3600s;`；是 HAProxy/Envoy 体系：要禁用 response buffering、`timeout server 3600s`。**不配会导致前端收不到实时消息或几分钟后断流** |
| SSO 回调路径 | `/auth/sso-callback` | 平台 Ingress 默认 path=`/` 已覆盖，无需单独规则；只需把这个完整 URL `https://<对外域名>/auth/sso-callback` 报给门户对接方做白名单登记 |
| Webhook IP 白名单 | `/api/v1/messages/webhooks/signal` | 接口当前**无鉴权**（第 10 节风险 #1），生产环境必须由平台 Ingress 限制只允许风控/组合系统的出口 IP 访问；找平台部做精确路径的 IP allowlist |

---

## 3. 如何连接公司内数据库（TDSQL for MySQL 8）

### 3.1 连接参数来源

后端通过 `app/core/db_tdsql.py` 的 `_ensure_engine_and_factory()` 建池，URL 由 `app/core/config.py::Settings.DATABASE_URL` 拼接：
```
mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset={DB_CHARSET}
```

修改 `config.json` 中的 6 项即可，**无需改任何代码**：

| 字段 | 生产示例 | 说明 |
|------|----------|------|
| `MAP_USE_SQLITE` | `false` | **生产必须 false**，否则会写本地 SQLite |
| `DB_HOST` | `tdsql-map-prod.intranet.company.com` | DBA 提供的 VIP 或域名 |
| `DB_PORT` | `5400` | TDSQL 默认 5400（不是 3306） |
| `DB_USER` | `map_app` | 业务账号，**最小权限**：DML + 必要 DDL |
| `DB_PASSWORD` | `<DBA 颁发>` | 不要硬编码，可改为读环境变量（见 3.3） |
| `DB_NAME` | `mapdb` | DBA 创建 |
| `DB_CHARSET` | `utf8mb4` | 不可改，否则中文乱码 |

连接池参数（`Settings` 内默认值，按需在 `config.json` 加同名 key 覆盖）：

| 字段 | 默认 | 调优建议 |
|------|------|----------|
| `DB_POOL_SIZE` | 10 | 每 worker × workers 数 ≤ DBA 给的 max_user_connections |
| `DB_MAX_OVERFLOW` | 20 | 突发并发缓冲 |
| `DB_POOL_RECYCLE` | 3600 | 必须小于 TDSQL `wait_timeout`（通常 28800） |

`db_tdsql.py` 已开启 `pool_pre_ping=True`，连接断开自动重连，TDSQL 主备切换无需重启。

### 3.2 连通性验证

在平台 Web Terminal 进入容器后先验证：
```bash
# 端口
nc -zv tdsql-map-prod.intranet.company.com 5400
# 账号 + 库
mysql -h tdsql-map-prod.intranet.company.com -P 5400 -u map_app -p mapdb -e "SHOW TABLES;"
```

应用层验证：
```bash
curl http://127.0.0.1:8000/api/v1/committee/meetings
```
返回 `[]` 或会议列表即正常；返回 500 看**平台日志页面**最近 200 行，常见错误：
- `Access denied` → DB_USER/DB_PASSWORD 错
- `Can't connect` → DB_HOST/DB_PORT 错或防火墙未放行
- `Unknown database` → 库名错或 DBA 未建库

### 3.3 密码不落盘（强烈推荐）

`config.json` 含明文密码不符合等保要求。改造方案（不改代码也可，但建议加 4 行）：
在 `app/core/config.py` 的 `_load_config()` 末尾追加：
```python
for k in ("DB_PASSWORD", "REDIS_PASSWORD", "SECRET_KEY"):
    if v := os.environ.get(k):
        data[k] = v
```
然后通过**平台密钥管理 / 加密环境变量**功能注入（见 2.3）；本地调试可临时用 `.env` 文件，但生产**禁止**把 secrets 提交进 Git 或写到普通环境变量框。

```
DB_PASSWORD=...
REDIS_PASSWORD=...
SECRET_KEY=<openssl rand -hex 32>
```


---

## 4. 如何与公司内 SSO 统一门户打通

### 4.1 整体登录流程

```
[1] 用户浏览器访问 https://map.intranet.company.com/  →  Nginx
[2] 未登录 → 前端跳转 https://sso.intranet.company.com/login?service=https://map.intranet.company.com/auth/sso-callback
[3] 用户在门户登录成功 → 门户 302 跳回:
       https://map.intranet.company.com/auth/sso-callback?ssoTokenId=<门户颁发的一次性 token>
[4] MAP 后端 GET /auth/sso-callback:
      ① 服务端调用门户接口 GET {SSO_VALIDATE_URL}?tokenId=<ssoTokenId>，拿到用户信息 JSON
      ② 按 portal_user_id 在 map_users 表查/创建本地用户
      ③ 签发 MAP 内部 JWT (HS256, sub=本地 user_id)
      ④ Set-Cookie: mapToken=<jwt>; HttpOnly; Secure; SameSite=Lax; Max-Age=ACCESS_TOKEN_EXPIRE_MINUTES*60
      ⑤ 302 重定向到 SSO_LOGIN_REDIRECT_URL（前端首页）
[5] 之后所有 /api/v1/** 请求自动带 Cookie；后端在 app/dependencies.py 解码 JWT 取 user_id
```

涉及代码：
- 回调路由：`app/modules/auth/sso_router.py::sso_callback`
- 门户校验：`app/modules/auth/services.py::validate_sso_token`
- 字段解析：`app/modules/auth/services.py::_parse_portal_response`
- JWT 签发：`app/core/security.py::create_access_token`
- 鉴权依赖：`app/dependencies.py::get_current_user_id` / `get_portal_user_id`

### 4.2 需要向门户/SSO 团队对齐的 5 件事

| 项 | 当前实现假设 | 必须确认 |
|----|------------|---------|
| 校验接口 URL | `SSO_VALIDATE_URL`（当前 dev 网关地址需替换） | 生产内网 URL，HTTP/HTTPS、是否需要双向证书 |
| 调用方式 | `GET ?tokenId=<id>` | 是否 GET？参数名是否 `tokenId`？是否需要在 Header 加 AppId/Signature |
| 返回 JSON 字段 | `userId / userName / displayName / email / department`（多别名兼容） | 实际字段名 → 与门户对齐后**改 `_parse_portal_response` 中的取值优先级** |
| `userId` 类型 | 当前代码 `_parse_portal_user_id` 强转 `int` | 若门户给字符串（如 "E12345"），需把 `map_users.portal_user_id` 改为 `String` 并去掉 `int()` 转换 |
| 回调地址注册 | `/auth/sso-callback` | 将完整 URL 报备给门户白名单 |

### 4.3 配置项（写在 `config.json`）

| 字段 | 生产示例 | 说明 |
|------|----------|------|
| `SSO_VALIDATE_URL` | `http://sso.intranet.company.com/wmuc/loginServer/loginValidateToken` | 门户颁发的 tokenId 校验接口 |
| `SSO_LOGIN_REDIRECT_URL` | `https://map.intranet.company.com/` | 登录成功后浏览器最终落地页（前端首页） |
| `SECRET_KEY` | `<openssl rand -hex 32>` | JWT HS256 签名密钥，**必须替换** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Cookie + JWT 过期时间（分钟） |
| `APP_ENV` | `production` | 控制 Cookie `Secure` 属性、关闭鉴权回退 |
| `DEBUG` | `false` | 关闭后取消 `user_id=1` 兜底 |

> ⚠️ **`APP_ENV=production` 后**：未携带有效 JWT 的请求一律 401；务必在 SSO 全链路联调通过后再切换。

### 4.4 字段映射改造点（最常见踩坑）

`_parse_portal_response` 当前按多个别名容错取值：
```python
user_id      = raw.get("userId") or raw.get("user_id") or raw.get("uid") or raw.get("id")
username     = raw.get("userName") or raw.get("username") or raw.get("loginName")
display_name = raw.get("displayName") or raw.get("display_name") or raw.get("name")
email        = raw.get("email")
department   = raw.get("department") or raw.get("deptName")
```
拿到门户接口真实样例后，**把上面优先级里属于本公司的字段名提到第一位**，避免别名顺序错乱拿到错误字段。

### 4.5 联调验证步骤

1. 直接 curl 校验接口（在容器 Web Terminal 内执行）：
   ```bash
   curl -v "${SSO_VALIDATE_URL}?tokenId=<门户测试 token>"
   ```
   能在 EXTERNAL_HTTP_TIMEOUT（默认 10s）内拿到 200 + JSON 才能继续。

2. 全链路测试：浏览器访问 `https://map.intranet.company.com/`，被门户拦截 → 登录 → 自动跳回 → 应有 `Set-Cookie: mapToken=...`，前端首页可正常加载。

3. 失败排查（按现象）：
   - 回调返回 `?error=invalid_token` → 门户校验返回的 JSON 里 `userId` 字段名不在别名列表中
   - 5xx + `门户 token 校验超时` → 防火墙/路由不通，或门户接口慢
   - 回调成功但前端仍 401 → Cookie 域名不匹配（Nginx 与后端 Host 头不一致）或前端没带 `credentials: 'include'`
   - `用户已被禁用` → `map_users.status=0`，DBA 数据问题


---

## 5. 配置表 · `config.json` 全量字段

> **位置**：通过平台"环境变量 / 配置中心"录入（见 2.3）；如果选了配置文件挂载模式，容器内路径由环境变量 `CONFIG_PATH` 指向。修改后需在平台 UI 保存并**重新发布 / 重启实例**才会生效。
> **源代码字段定义**：`app/core/config.py::Settings`。

### 5.1 基础与安全

| 字段 | 类型 | 生产取值 | 必填 | 说明 |
|---|---|---|---|---|
| `APP_ENV` | string | `production` | ✅ | 取值 `development/staging/production`。生产必须为 `production`，否则 SECRET_KEY 校验放行、Cookie 不带 Secure |
| `APP_NAME` | string | `MAP Backend` | ⛔ | 仅文档与首页展示用 |
| `APP_VERSION` | string | `0.1.0` | ⛔ | 出现在 `/health` |
| `DEBUG` | bool | `false` | ✅ | 生产必须 `false`，否则未认证请求会被回退为 `user_id=1` |
| `SECRET_KEY` | string | `<openssl rand -hex 32>` | ✅ | JWT 签名密钥；`APP_ENV=production` 且值为 `change-me-in-production` 时启动会直接报错 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | `480` | ⛔ | 单位分钟，决定 JWT 与 Cookie 寿命 |
| `CORS_ORIGINS` | string | `https://map.intranet.company.com` | ✅ | 逗号分隔多个域；**生产不能 `*`** |

### 5.2 数据库 / Redis / MQ

| 字段 | 类型 | 生产取值 | 必填 | 说明 |
|---|---|---|---|---|
| `MAP_USE_SQLITE` | bool | `false` | ✅ | 生产必须 `false` |
| `DB_HOST` | string | `tdsql-map-prod.intranet.company.com` | ✅ | DBA 提供 |
| `DB_PORT` | int | `5400` | ✅ | TDSQL 默认 5400 |
| `DB_USER` | string | `map_app` | ✅ | 业务账号 |
| `DB_PASSWORD` | string | `<DBA 颁发>` | ✅ | 建议改为环境变量注入（见 3.3） |
| `DB_NAME` | string | `mapdb` | ✅ | |
| `DB_CHARSET` | string | `utf8mb4` | ✅ | 不可改 |
| `DB_POOL_SIZE` | int | `10` | ⛔ | 见 3.1 |
| `DB_MAX_OVERFLOW` | int | `20` | ⛔ | |
| `DB_POOL_RECYCLE` | int | `3600` | ⛔ | 秒 |
| `REDIS_HOST` | string | `redis-map.intranet.company.com` | ✅ | 由运维提供。未配置时门户快照接口走慢路径但不影响功能 |
| `REDIS_PORT` | int | `6379` | ✅ | |
| `REDIS_PASSWORD` | string | `<运维颁发>` | ⛔ | 无密码留空 |
| `REDIS_DB` | int | `0` | ⛔ | 多套环境共用集群时区分 |
| `REDIS_MAX_CONNECTIONS` | int | `50` | ⛔ | |
| `ROCKETMQ_NAME_SERVER` | string | `rmq-ns.intranet.company.com:9876` | ⚠️ | 未配置 RocketMQ 时 MQ 生产者降级 stub，**异步指令不会被处理**（见 6.2） |
| `ROCKETMQ_PRODUCER_GROUP` | string | `MAP_PRODUCER_GROUP_PROD` | ⛔ | 按环境后缀区分 |
| `ROCKETMQ_CONSUMER_GROUP` | string | `MAP_CONSUMER_GROUP_PROD` | ⛔ | 同上 |
| `ROCKETMQ_TOPIC` | string | `MAP_EVENTS_PROD` | ⛔ | 需要运维在 RocketMQ 控制台预创建 Topic |

### 5.3 SSO 与外部系统

| 字段 | 类型 | 生产取值 | 必填 | 说明 |
|---|---|---|---|---|
| `SSO_VALIDATE_URL` | string | `http://sso.intranet.company.com/wmuc/loginServer/loginValidateToken` | ✅ | 门户 token 校验接口 |
| `SSO_LOGIN_REDIRECT_URL` | string | `https://map.intranet.company.com/` | ✅ | 登录成功后浏览器最终落地 URL |
| `PORTFOLIO_SYS_URL` | string | `http://portfolio-sys.intranet.company.com` | ⚠️ | 留空将使用 Mock 适配器，门户首页头寸为假数据 |
| `RISK_SYS_URL` | string | `http://risk-sys.intranet.company.com` | ⚠️ | 留空使用 Mock |
| `EXTERNAL_HTTP_TIMEOUT` | float | `10.0` | ⛔ | 调用所有外部系统的统一超时（秒） |
| `EXTERNAL_HTTP_RETRIES` | int | `3` | ⛔ | BaseAdapter 指数退避次数 |

> **必填列说明**：✅ = 上线前必须正确配置；⚠️ = 不配置功能可用但有副作用；⛔ = 可保持默认。


---

## 6. 配置表 · 接口与外部系统对接矩阵

> 列含义：
> - **MAP DB** = TDSQL `mapdb`（本应用自管，见第 3 节）
> - **Redis** = 缓存/SSE 总线
> - **SSO 门户** = `SSO_VALIDATE_URL`
> - **组合系统** = `PORTFOLIO_SYS_URL`（适配器：`portfolio_sys.py`）
> - **风控系统** = `RISK_SYS_URL`（适配器：`risk_sys.py`）
> - **RocketMQ** = `ROCKETMQ_NAME_SERVER`
> - ✓ 必需；○ 可选/降级；— 不依赖

### 6.1 业务 API 端点（前端调用）

| 路径 | 方法 | 模块 | MAP DB | Redis | SSO 门户 | 组合系统 | 风控系统 | RocketMQ | 备注 |
|---|---|---|:---:|:---:|:---:|:---:|:---:|:---:|---|
| `/health` | GET | 健康 | — | — | — | — | — | — | 无认证 |
| `/auth/sso-callback` | GET | auth/sso | ✓ | — | ✓ | — | — | — | 门户回调，唯一调用 SSO 校验接口的入口 |
| `/api/v1/auth/me` | GET | auth | ✓ | — | — | — | — | — | 读 `map_users` |
| `/api/v1/workspace/portal-snapshot` | GET | workspace | ✓ | ○ | — | ✓ | — | — | 读 `ic_resolutions` + 调组合系统；Redis 命中走快路径；外部失败返回 stale |
| `/api/v1/committee/page-context` | GET | committee | ✓ | — | — | — | — | — | 读最新决议与投票摘要 |
| `/api/v1/committee/meetings` | GET / POST | committee | ✓ | — | — | — | — | — | 读写 `ic_meetings` |
| `/api/v1/committee/meetings/{id}` | DELETE | committee | ✓ | — | — | — | — | — | 软删除 |
| `/api/v1/committee/meetings/{id}/submit-vote` | POST | committee | ✓ | — | — | — | — | — | 读写 `ic_vote_records` |
| `/api/v1/committee/meetings/{id}/publish` | POST | committee | ✓ | — | — | — | — | — | 计票聚合写 `ic_resolutions` |
| `/api/v1/committee/meetings/{id}/resolution` | POST | committee | ✓ | — | — | — | — | — | 主任委员决议 `ic_chair_resolutions` |
| `/api/v1/committee/mixed/submit` | POST | committee/mixed | ✓ | — | — | — | — | — | 读写 `mixed_submissions` |
| `/api/v1/committee/mixed/sessions` | GET | committee/mixed | ✓ | — | — | — | — | — | |
| `/api/v1/committee/mixed/sessions/history` | GET | committee/mixed | ✓ | — | — | — | — | — | |
| `/api/v1/committee/mixed/remind` | POST | committee/mixed | ✓ | — | — | — | — | — | 当前 stub，未来对接公司 IM/邮件时新增依赖 |
| `/api/v1/asset-allocation/asset-classes` | GET | asset_allocation | ✓ | — | — | — | — | — | |
| `/api/v1/asset-allocation/drafts` | GET | asset_allocation | ✓ | — | — | — | — | — | 读 `saa_drafts` |
| `/api/v1/asset-allocation/drafts/{id}` | GET | asset_allocation | ✓ | — | — | — | — | — | |
| `/api/v1/asset-allocation/drafts/calculate` | POST | asset_allocation | ✓ | — | — | — | — | — | 纯本地计算 |
| `/api/v1/asset-allocation/drafts/{id}/submit` | POST | asset_allocation | ✓ | — | — | — | — | — | |
| `/api/v1/asset-allocation/drafts/{id}/approve` | POST | asset_allocation | ✓ | — | — | — | — | — | |
| `/api/v1/asset-allocation/drafts/{id}/reject` | POST | asset_allocation | ✓ | — | — | — | — | — | |
| `/api/v1/orchestrator/commands` | POST | orchestrator | ✓ | — | — | △ | — | △ | 路由表见 6.2；MQ 模式发 RocketMQ，SYNC 模式调组合系统 |
| `/api/v1/orchestrator/commands/{task_id}` | GET | orchestrator | ✓ | — | — | — | — | — | 读 `pending_commands` |
| `/api/v1/messages/events/stream` | GET | message_center | — | ✓ | — | — | — | — | SSE 长连接，Redis Pub/Sub；Nginx 必须关 buffer |
| `/api/v1/messages/webhooks/signal` | POST | message_center | — | ✓ | — | — | — | — | **入站**：外部系统主动推事件给 MAP |
| `/docs`, `/redoc`, `/` | GET | meta | — | — | — | — | — | — | Swagger / 首页；建议在 Nginx 层限制内网 IP |

△ = 同一端点根据 `command_type` 路由到不同后端，见下一节。

### 6.2 `/api/v1/orchestrator/commands` 指令路由表

源：`app/modules/orchestrator/commands.py::COMMAND_ROUTES` + `app/modules/consumers/handlers.py`

| `command_type` | 分发模式 | 落地 |
|---|---|---|
| `SUBMIT_SAA_FOR_APPROVAL` | MQ | RocketMQ → 消费者改 `saa_drafts` 状态 |
| `PUBLISH_SAA_RESULT` | MQ | RocketMQ → 消费者经 `scenario_assembler` 推 SSE |
| `TRIGGER_PORTFOLIO_REBALANCE` | MQ | RocketMQ → 消费者调**组合系统** `POST /portfolios/rebalance` |
| `SYNC_PORTFOLIO_SNAPSHOT` | SYNC | 同步调**组合系统** `GET /portfolios/{id}/snapshot` |
| `NOTIFY_IC_RESOLUTION_PUBLISHED` | MQ | RocketMQ → 当前仅打日志，扩展点 |
| `REQUEST_RESEARCH_REPORT` | MQ | RocketMQ → 研究系统适配器（**TODO**，未实现） |

> ⚠️ **RocketMQ 不可用时**：MQ 类指令会标记 `FAILED` 写入 `pending_commands`，但不会自动重试；运维需要定时任务或人工处理。

### 6.3 入站 Webhook（外部系统 → MAP）

| 端点 | 方法 | 调用方 | 鉴权 | 现状 |
|---|---|---|---|---|
| `/api/v1/messages/webhooks/signal` | POST | 风控 / 组合 / 研究系统 | **当前无鉴权** ⚠️ | 上线前需补：①Nginx IP 白名单 限制为内部系统出口 IP；②或加 Header 签名校验（`X-Signature: HMAC-SHA256(secret, body)`） |

Body 结构（`webhooks.py::RawSignal`）：
```json
{
  "source": "risk_sys",
  "event_type": "RISK_ALERT",
  "payload": { "portfolio_id": "MAP-MAIN-001", "level": "HIGH" },
  "occurred_at": "2026-05-13T10:00:00Z",
  "idempotency_key": "risk-evt-20260513-001"
}
```

---

## 7. 网络与防火墙白名单清单

向运维提交的端口/方向开通申请：

| 方向 | 源 | 目标 | 端口/协议 | 用途 |
|---|---|---|---|---|
| 出向 | MAP 应用容器（平台出口） | TDSQL VIP | TCP/5400 | 数据库连接 |
| 出向 | MAP 应用容器（平台出口） | Redis VIP | TCP/6379 | 缓存/SSE 总线 |
| 出向 | MAP 应用容器（平台出口） | RocketMQ NameServer | TCP/9876 | MQ NameSrv（首期 stub 模式可不申请） |
| 出向 | MAP 应用容器（平台出口） | RocketMQ Broker | TCP/10911, 10912, 10909 | MQ Broker（首期 stub 模式可不申请） |
| 出向 | MAP 应用容器（平台出口） | 门户 SSO 校验接口 | TCP/80 或 443 | `SSO_VALIDATE_URL` |
| 出向 | MAP 应用容器（平台出口） | 组合系统 | TCP/80 或 443 | `PORTFOLIO_SYS_URL` |
| 出向 | MAP 应用容器（平台出口） | 风控系统 | TCP/80 或 443 | `RISK_SYS_URL` |
| 入向 | 风控/组合系统出口 IP | 平台对外域名 `:443` | TCP/443 | `/api/v1/messages/webhooks/signal`，平台 Ingress 侧做精确路径 IP 白名单（见 2.5） |
| 入向 | 浏览器（员工内网） | 平台对外域名 `:443` | TCP/443 | 前端访问 |

> "平台出口 IP / VIP / 对外域名" 由平台部提供，向运维提工单时把这一列替换成具体地址再发出去。代码部署 + 流水线侧（GitLab、内部 PyPI 镜像、基础镜像仓）的出向不需要你申请——平台已经配好。

---

## 8. 上线 Checklist（按顺序勾选）

### 8.1 代码与依赖

- [ ] 流水线 `pip install -r requirements.txt` 全部成功（走内部 PyPI 镜像，无外网回退）
- [ ] 镜像内 `python -c "from app.main import app; print('ok')"` 无 ImportError
- [ ] 启用 RocketMQ：Dockerfile 已 `COPY librocketmq.so` 且 `rocketmq-client-python` 安装成功（首期可跳过）

### 8.2 配置

- [ ] `/etc/map/config.json` 已就位，权限 0600，owner = mapapp
- [ ] `APP_ENV=production`、`DEBUG=false`
- [ ] `SECRET_KEY` 已换成 `openssl rand -hex 32` 生成的强随机值
- [ ] `CORS_ORIGINS` 已改为前端实际域名（非 `*`）
- [ ] `SSO_VALIDATE_URL` / `SSO_LOGIN_REDIRECT_URL` 已对齐门户提供的真实地址
- [ ] 数据库 6 项 (`DB_*`) 已填生产值，密码不在 `config.json` 明文（推荐 3.3 改造）
- [ ] `PORTFOLIO_SYS_URL` / `RISK_SYS_URL`：① 已对接的填真实地址；② 暂未对接的明确留空（团队周知会走 Mock）

### 8.3 基础设施联通

- [ ] `nc -zv` 验证 5 类外部资源（DB / Redis / MQ / SSO / 组合/风控系统）端口可达
- [ ] DBA 已建库 `mapdb` + 业务账号；建表脚本已成功执行；`SHOW TABLES` 返回 8 张表
- [ ] RocketMQ 控制台已创建 `MAP_EVENTS_PROD` Topic 及消费者组
- [ ] 门户白名单已登记 `https://map.intranet.company.com/auth/sso-callback`

### 8.4 服务自检

- [ ] 平台部署页面状态 = "运行中"，副本数全部就绪、近期无重启
- [ ] 平台日志页面最近 200 行无 ERROR；可见 `RocketMQ consumer worker started (sdk=False)`（首期 stub 模式正常）或 `sdk=True`（已启用 SDK）
- [ ] 容器 Web Terminal 内 `curl http://127.0.0.1:8000/health` 返回 `{"status":"ok","version":"...","env":"production"}`
- [ ] 平台对外域名 `https://<域名>/health` 返回同上（验证 Ingress 链路通）
- [ ] 浏览器全链路：访问首页 → 跳门户 → 登录 → 跳回 → Cookie 已下发 → 前端首屏数据正常
- [ ] `/api/v1/workspace/portal-snapshot` 返回的 `positions` 非 null（说明组合系统已对接）
- [ ] 故意造一次未带 Cookie 的 `/api/v1/auth/me` 请求 → 必须 401（验证鉴权未走回退）

### 8.5 运维基础

- [ ] 日志接公司日志平台（建议 `--log-config /etc/map/logging.json` 输出 JSON）
- [ ] 平台健康检查已指向 `GET /health`，并验证过实例异常时平台会自动重建
- [ ] 定时备份 `mapdb`（DBA 侧）
- [ ] `/api/v1/messages/webhooks/signal` 已加 IP 白名单或签名校验

---

## 9. 监控与日志关键点

| 监控项 | 来源 | 告警条件 |
|---|---|---|
| 健康检查 | `GET /health` | 30s 连续失败 |
| MQ 消费者状态 | 日志 `RocketMQ consumer worker started (sdk=True)` | 启动后 sdk=False 即告警 |
| `pending_commands.status='FAILED'` 数量 | DB 查询 | 5 分钟新增 > N |
| 门户校验失败率 | 日志 `门户 token 校验超时/失败` | 5 分钟错误率 > 5% |
| 外部 Adapter 失败率 | 日志 `Portfolio adapter failed` | 同上 |
| DB 连接池占用 | SQLAlchemy 日志 | 接近 `pool_size + max_overflow` |
| `portal-snapshot` 走 stale 比例 | 响应字段 `is_stale=true` | 高于阈值意味外部系统/Redis 有问题 |

日志默认输出到 stdout，由公司日志平台自动采集，**不要在容器内写文件日志**——容器重建即丢。如果平台日志平台支持 JSON 解析，可以把 `logging.json` 放进仓库，启动命令加 `--log-config logging.json`，输出结构化日志便于检索。

---

## 10. 已知风险与改进项（建议在上线后第一个迭代修复）

| # | 风险 | 影响 | 建议 |
|---|---|---|---|
| 1 | `/api/v1/messages/webhooks/signal` 无鉴权 | 任意能访问 API 的内网主机可注入伪事件，触发 SSE 推送 | 加 IP 白名单 + HMAC 签名 |
| 2 | RocketMQ 消费者与 Web 进程绑定（在 lifespan 启动） | Web 多副本时消息会被重复消费 | 拆分独立 entrypoint，或只在 1 副本启用消费 |
| 3 | `map_users.portal_user_id` 用 `BigInteger` 且强制 `int()` 转换 | 门户用户 ID 若为字符串（含字母）会直接 401 | 与门户对齐 ID 类型后改 `String(64)` |
| 4 | `SECRET_KEY` 校验只拦截字面值 `"change-me-in-production"` | `dev-secret-key-change-in-production` 等弱值能通过 | 校验扩展为长度/熵阈值检查 |
| 5 | `register_and_dispatch` 把 `db.commit()` 放在路由层调用之后 | 分发失败仍会 commit，使 `pending_commands` 留下未投递记录 | 增加补偿定时任务扫描 PENDING/FAILED 重试 |
| 6 | `webhooks/signal` 用 `asyncio.create_task` 起后台任务 | 进程退出时任务可能丢失 | 改投 RocketMQ 异步处理 |
| 7 | 缺 Alembic 迁移基线 | DDL 变更只能 `create_all`，无法回滚 | 上线后立即生成 baseline `alembic stamp head` |

---

## 附录 A · 生产 `config.json` 模板

```json
{
  "APP_ENV": "production",
  "APP_NAME": "MAP Backend",
  "APP_VERSION": "0.1.0",
  "DEBUG": false,
  "SECRET_KEY": "REPLACE_WITH_OPENSSL_RAND_HEX_32",
  "ACCESS_TOKEN_EXPIRE_MINUTES": 480,
  "CORS_ORIGINS": "https://map.intranet.company.com",

  "MAP_USE_SQLITE": false,
  "DB_HOST": "tdsql-map-prod.intranet.company.com",
  "DB_PORT": 5400,
  "DB_USER": "map_app",
  "DB_PASSWORD": "REPLACE_OR_USE_ENV",
  "DB_NAME": "mapdb",
  "DB_CHARSET": "utf8mb4",
  "DB_POOL_SIZE": 10,
  "DB_MAX_OVERFLOW": 20,
  "DB_POOL_RECYCLE": 3600,

  "REDIS_HOST": "redis-map.intranet.company.com",
  "REDIS_PORT": 6379,
  "REDIS_PASSWORD": "",
  "REDIS_DB": 0,
  "REDIS_MAX_CONNECTIONS": 50,

  "ROCKETMQ_NAME_SERVER": "rmq-ns.intranet.company.com:9876",
  "ROCKETMQ_PRODUCER_GROUP": "MAP_PRODUCER_GROUP_PROD",
  "ROCKETMQ_CONSUMER_GROUP": "MAP_CONSUMER_GROUP_PROD",
  "ROCKETMQ_TOPIC": "MAP_EVENTS_PROD",

  "SSO_VALIDATE_URL": "http://sso.intranet.company.com/wmuc/loginServer/loginValidateToken",
  "SSO_LOGIN_REDIRECT_URL": "https://map.intranet.company.com/",

  "PORTFOLIO_SYS_URL": "http://portfolio-sys.intranet.company.com",
  "RISK_SYS_URL": "http://risk-sys.intranet.company.com",

  "EXTERNAL_HTTP_TIMEOUT": 10.0,
  "EXTERNAL_HTTP_RETRIES": 3
}
```

