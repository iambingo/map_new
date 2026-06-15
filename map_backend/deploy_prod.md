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

> 当前 `consumer_worker` 在 `lifespan` 内自动启动，单实例即可工作。**多实例水平扩展时需先做消费者拆分**，否则每个实例会重复消费同一消息。首期 stub 模式无需处理。

---

## 2. 内网部署步骤

### 2.1 代码侧准备

**部署模式**：公司 PaaS 平台已建好容器运行时，开发只交付**代码**。流程是 push 到 GitLab 测试分支 → 平台 UI 点 "发布" → 平台拉代码、装依赖、起进程、挂域名。

代码侧（仓库根目录）必须就位的文件：

| 文件 | 状态 | 作用 |
|------|------|------|
| `requirements.txt` | ✅ 已有 | 平台执行 `pip install -r requirements.txt` 装依赖（走平台内置的内部 PyPI 镜像） |
| `app/` | ✅ 已有 | FastAPI 应用包，入口 `app.main:app` |
| `run.sh` | ✅ 已有 | 一键启动脚本：装依赖 → 建库 → 建表 → 起 Uvicorn（见 2.4） |
| `.gitignore` | ✅ 已有 | 已排除 `map_wheels/`、`.claude/`、`venv/` |
| `.dockerignore` | ✅ 已有 | 防御性配置：若平台构建走 Docker 体系，这份排除清单会被识别，避免把 `.venv/`、`__pycache__/`、`.claude/`、本地 SQLite、`deploy_prod.md` 等本地开发噪声打进镜像 |

**不需要**：`Dockerfile`、K8s YAML、wheel 离线包——平台都管。

#### 2.1.1 需要向平台部确认

| # | 项 | 要求 |
|---|---|---|
| 1 | Python 版本 | **3.10**（与 wheel ABI 匹配） |
| 2 | 内部 PyPI | 确认能解析 `pydantic-core`、`cryptography`、`bcrypt`、`uvloop` 等 C 扩展 |
| 3 | 启动命令 | 见 2.4 |
| 4 | 监听端口 | `8000` |
| 5 | 健康检查 | `GET /health` → 200 |
| 6 | 配置注入 | 环境变量方式（见 2.3） |

#### 2.1.2 RocketMQ SDK

`rocketmq-client-python` 依赖系统库 `librocketmq.so`。**首期跳过**——已注释掉，代码自动降级 stub 模式，不阻断启动。启用时需平台部安装系统库并取消 `requirements.txt` 中的注释。

### 2.2 数据库初始化

**`run.sh` 已内置自动建库建表逻辑**，启动时自动执行，无需手工操作：

1. **建库**：通过 `INFORMATION_SCHEMA.SCHEMATA` 检查数据库是否存在，不存在则 `CREATE DATABASE`；已存在则跳过。
2. **建表**：通过 SQLAlchemy `metadata.create_all` 幂等建表（`CREATE TABLE IF NOT EXISTS`），已建表无副作用。

```bash
# run.sh 内部流程（伪代码）：
# 1. 从 config.json 读取 DB_HOST/DB_PORT/DB_USER/DB_PASSWORD/DB_NAME
# 2. 用 pymysql 检查库是否存在 → 不存在则 CREATE DATABASE
# 3. 导入所有 ORM 模型 → Base.metadata.create_all()
# 4. 启动 Uvicorn
```

> 若 DBA 已手动建库，`run.sh` 会自动检测并跳过建库步骤。所有操作均为幂等，重复执行安全。

**手动建库（可选，仅 DBA 需要）**：

```sql
-- DBA 手动建库（run.sh 可自动完成，此命令仅保留参考）：
-- CREATE DATABASE pawmmapdata DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

涉及的表（合计 8 张，均无物理外键）：`map_users`、`ic_meetings`、`ic_vote_records`、`ic_resolutions`、`ic_chair_resolutions`、`mixed_submissions`、`pending_commands`、`saa_drafts`（具体以模型 `__tablename__` 为准）。

### 2.3 运行时配置注入

`config.json` **绝不进 Git**。在平台的"环境变量 / 配置中心"页面分两类录入：

| 分类 | 内容 | 平台 UI 填法 |
|------|------|--------------|
| 非敏感 | `APP_ENV=production`、`DEBUG=false`、`DB_HOST`、`DB_PORT`、`DB_NAME`、`DB_USER`、`DB_CHARSET`、`REDIS_HOST`、`REDIS_PORT`、`SSO_LOGIN_URL`、`SSO_VALIDATE_URL`、`SSO_LOGIN_REDIRECT_URL`、`PORTFOLIO_SYS_URL`、`RISK_SYS_URL` 等 | "环境变量" 直接键值录入 |
| 敏感（凭据） | `DB_PASSWORD`、`REDIS_PASSWORD`、`SECRET_KEY`、`PORTAL_CLIENT_SECRET` | 平台一般有"密钥/Secret 管理"或"加密配置"开关，把这几项勾上加密；**不要直接写进普通环境变量框** |

**配置加载机制**（代码 `app/core/config.py` 实现）：

1. 先读 `config.json` 作为**基础配置模板**（同一份代码推送到所有环境，config.json 不变）
2. 同名环境变量**自动覆盖** config.json 中的值（`SSO_VALIDATE_URL`、`DB_HOST` 等通过平台 UI 按环境录入不同值）
3. 敏感字段也可以走环境变量覆盖（见 3.3），**不需要**写进 config.json

> 部署方式：**同一份 config.json + 平台按环境注入不同环境变量**。三套环境只需维护一份代码和一份 config.json 模板，差异化配置全部在平台 UI 上管理。



### 2.4 启动命令

平台的"启动命令 / Entrypoint"配置项里有两种方式，**推荐方式 A**：

#### 方式 A：使用 `run.sh`（推荐）

```bash
bash run.sh
```

`run.sh` 内部流程：
1. 读取 `config.json`（可通过 `CONFIG_PATH` 环境变量覆盖路径）
2. `pip install -r requirements.txt` 安装依赖（走内部 PyPI 镜像，可通过 `INTERNAL_PYPI` 环境变量覆盖）
3. 检查并创建数据库（幂等：已建则跳过）
4. 首次建表（幂等：已建表则无副作用）
5. `exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers --forwarded-allow-ips=*`

可配置环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `CONFIG_PATH` | `./config.json` | config.json 路径 |
| `INTERNAL_PYPI` | （空） | 内部 PyPI 镜像地址，留空则使用 pip 默认源 |
| `WORKERS` | `4` | Uvicorn worker 数量 |
| `PORT` | `8000` | 监听端口 |

#### 方式 B：直接启动（适合已预装依赖的场景）

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4 --proxy-headers --forwarded-allow-ips=*
```

逐项说明：

| 参数 | 必须 | 原因 |
|------|------|------|
| `--host 0.0.0.0` | ✅ | 容器内必须监听全部网卡，否则平台健康检查打不进来 |
| `--port 8000` | ⚠️ | 与平台 UI 里填的"监听端口"一致即可；如果平台强制要 8080，把这里和端口字段一起改 |
| `--workers 4` | 建议 | 单 Pod 起 4 个 worker 进程；按平台分配的 CPU 配额调（一般 worker 数 ≈ CPU 核数） |
| `--proxy-headers --forwarded-allow-ips=*` | ✅ | 平台 Ingress 前置代理，必须信任 `X-Forwarded-*` 头，否则 SSO 回调 Cookie 的 Secure/HttpOnly 判断会错 |

> **`--workers` 与 RocketMQ**：首期 stub 模式 `--workers 4` 没问题。启用 RocketMQ 后需改为 `--workers 1` 或做消费者拆分。

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
| SSO 回调路径 | `/`（根路径） | 门户回调 URL = **我方根 URL** `https://<对外域名>/`，由门户在登录成功后追加 `?ssoTokenId=xxx`。平台 Ingress 默认 path=`/` 已覆盖；把根 URL 报给门户对接方做白名单登记即可 |
| Webhook IP 白名单 | `/api/v1/messages/webhooks/signal` | 接口当前**无鉴权**（第 10 节风险 #1），生产环境必须由平台 Ingress 限制只允许风控/组合系统的出口 IP 访问；找平台部做精确路径的 IP allowlist |

---

## 3. 如何连接公司内数据库（TDSQL for MySQL 8）

### 3.1 连接参数来源

后端通过 `app/core/db_tdsql.py` 的 `_ensure_engine_and_factory()` 建池，URL 由 `app/core/config.py::Settings.DATABASE_URL` 拼接：
```
mysql+aiomysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}?charset={DB_CHARSET}
```

拼接后实际 URL：`mysql+aiomysql://deployop:j3eKJSbX29e3@t0pawmmapdata-my.db.qa.pab.com.cn:3306/pawmmapdata?charset=utf8mb4`

修改环境变量即可（同名覆盖 config.json），**无需改任何代码**：

| 字段 | 生产示例 | 说明 |
|------|----------|------|
| `MAP_USE_SQLITE` | `false` | **生产必须 false** |
| `DB_HOST` | `t0pawmmapdata-my.db.qa.pab.com.cn` | DBA 提供的 VIP 或域名 |
| `DB_PORT` | `3306` | 标准 MySQL 端口 |
| `DB_USER` | `deployop` | 最高权限账号（首期跑通用） |
| `DB_PASSWORD` | `<环境变量注入>` | 首期可明文配置，生产建议走密钥管理 |
| `DB_NAME` | `pawmmapdata` | DBA 已建库 |
| `DB_CHARSET` | `utf8mb4` | 不可改 |

连接池参数（`Settings` 内默认值，按需在 `config.json` 加同名 key 覆盖）：

| 字段 | 默认 | 调优建议 |
|------|------|----------|
| `DB_POOL_SIZE` | 10 | 每 worker × workers 数 ≤ DBA 给的 max_user_connections |
| `DB_MAX_OVERFLOW` | 20 | 突发并发缓冲 |
| `DB_POOL_RECYCLE` | 3600 | 必须小于 TDSQL `wait_timeout`（通常 28800） |

`db_tdsql.py` 已开启 `pool_pre_ping=True`，连接断开自动重连，TDSQL 主备切换无需重启。

### 3.2 连通性验证

在平台 Web Terminal 进入容器后验证：
```bash
nc -zv t0pawmmapdata-my.db.qa.pab.com.cn 3306
mysql -h t0pawmmapdata-my.db.qa.pab.com.cn -P 3306 -u deployop -p pawmmapdata -e "SHOW TABLES;"
```
常见错误：`Access denied` → 密码错；`Can't connect` → 网络不通；`Unknown database` → 库未建。

### 3.3 密码不落盘

敏感字段（`DB_PASSWORD`、`REDIS_PASSWORD`、`SECRET_KEY`）**不要写在 config.json 明文里**，通过平台密钥管理 / 加密环境变量注入；代码 `_load_config()` 会自动用环境变量覆盖 config.json 同名字段。


---

## 4. 如何与公司内 SSO 统一门户打通

### 4.1 整体登录流程

```
[1] 用户浏览器访问 https://<map 对外域名>/  →  平台 Ingress  →  MAP 后端
[2] 后端检测到无 ssoTokenId 且无 mapToken Cookie → 前端把浏览器跳到门户登录页：
       ${SSO_LOGIN_URL}?url=https://<map 对外域名>/
    （门户接受参数 url 作为登录成功后的回跳地址）
[3] 用户在门户登录成功 → 门户 302 跳回**我方根 URL**:
       https://<map 对外域名>/?ssoTokenId=<门户颁发的一次性 token>
[4] MAP 后端 GET / 命中 `root_or_sso_callback`，因带 ssoTokenId 走回调分支:
      ① 服务端调用门户接口 GET {SSO_VALIDATE_URL}?tokenId=<ssoTokenId>，拿到 `{"data":{"userId":"xxx","userName":"xxx","realName":"xxx","mailAddr":"xxx"}}`
      ② 按 portal_user_id 在 map_users 表查/创建本地用户
      ③ 签发 MAP 内部 JWT (HS256, sub=本地 user_id)
      ④ Set-Cookie: mapToken=<jwt>; HttpOnly; Secure; SameSite=Lax; Max-Age=ACCESS_TOKEN_EXPIRE_MINUTES*60
      ⑤ 302 重定向到 SSO_LOGIN_REDIRECT_URL（前端首页）
[5] 之后所有 /api/v1/** 请求自动带 Cookie；后端在 app/dependencies.py 解码 JWT 取 user_id
```

涉及代码：`app/modules/auth/sso_router.py`（回调路由）、`app/modules/auth/services.py`（门户校验）、`app/core/security.py`（JWT 签发）。

### 4.2 门户对接确认清单

| 项 | 状态 | 备注 |
|----|------|------|
| 调用方式 | ✅ 已确认 | GET 请求，URL 带 `?tokenId=xxx` 查询参数即可 |
| 返回 JSON 结构 | ✅ 已确认 | `{"data":{"userId","userName","realName","mailAddr"}}`，代码已适配 |
| 门户登录页 URL | ⚠️ 待确认 | `SSO_LOGIN_URL` 三档地址是否可用，跳转参数名是否为 `url` |
| 校验接口 HTTPS | ⚠️ 待确认 | PRD 环境是否需要 HTTPS 或双向证书 |
| `userId` 类型 | ⚠️ 待确认 | 若门户给字符串（如 "E12345"），需改 `map_users.portal_user_id` 为 `String(64)` |
| 回调地址注册 | ⚠️ 待注册 | 把**我方根 URL** `https://<map 对外域名>/` 报备给门户白名单 |

### 4.3 配置项（按环境录入平台环境变量）

| 字段 | DEV | FAT | PRD | 说明 |
|------|-----|-----|-----|------|
| `SSO_LOGIN_URL` | `http://wm.dev.paic.com.cn/lckj/pawm-uc/account_login.html` | `http://wm.stg.paic.com.cn/lckj/pawm-uc/account_login.html` | `http://wm.paic.com.cn/lckj/pawm-uc/account_login.html` | 门户登录页（浏览器跳转） |
| `SSO_VALIDATE_URL` | `http://pawm-pfp-service-gateway.dev.pab.com.cn/wmuc/loginServer/loginValidateToken` | `http://pawm-pfp-83022-gateway.fat001.qa.pab.com.cn/wmuc/loginServer/loginValidateToken` | `http://pawm-pfp-83022-auth-gateway.pab.com.cn/wmuc/loginServer/loginValidateToken` | 门户 tokenId 校验接口，GET 请求 URL 带 `?tokenId=xxx` |
| `SSO_LOGIN_REDIRECT_URL` | `https://<map dev 域名>/` | `https://<map fat 域名>/` | `https://<map prd 域名>/` | 登录成功后浏览器最终落地 URL |

其余跨环境通用字段：

| 字段 | 取值 | 说明 |
|------|------|------|
| `SECRET_KEY` | `<openssl rand -hex 32>` | JWT HS256 签名密钥，**每环境独立、必须替换** |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `480` | Cookie + JWT 过期时间（分钟） |
| `APP_ENV` | `production` | 控制 Cookie `Secure` 属性、关闭鉴权回退 |
| `DEBUG` | `false` | 关闭后取消 `user_id=1` 兜底 |

> ⚠️ **`APP_ENV=production` 后**：未携带有效 JWT 的请求一律 401；务必在 SSO 全链路联调通过后再切换。

### 4.4 门户字段映射（已确认）

门户返回 `{"data": {...}}`，`_parse_portal_response` 已按以下优先级解析：

| 本地字段 | 门户字段优先级 |
|---------|---------------|
| `user_id` | `userId` → `user_id` → `uid` → `id` |
| `username` | `userName` → `username` → `loginName` |
| `display_name` | `realName` → `displayName` → `display_name` → `name` |
| `email` | `mailAddr` → `email` |
| `department` | `department` → `deptName` |

### 4.5 联调验证步骤

1. 直接 curl 校验接口（在容器 Web Terminal 内执行）：
   ```bash
   curl -v "${SSO_VALIDATE_URL}?tokenId=<门户测试 token>"
   ```
   能在 EXTERNAL_HTTP_TIMEOUT（默认 10s）内拿到 200 + JSON 才能继续。

2. 全链路测试：浏览器访问 `https://map.intranet.company.com/`，被门户拦截 → 登录 → 自动跳回 → 应有 `Set-Cookie: mapToken=...`，前端首页可正常加载。

3. 失败排查：
   - 没跳门户 → 前端未实现跳转逻辑或 `SSO_LOGIN_URL` 未配
   - `?error=invalid_token` → `userId` 字段名不在解析别名中
   - 5xx + `超时` → 防火墙不通或门户接口慢
   - 回调成功但前端仍 401 → Cookie 域名不匹配或前端未带 `credentials: 'include'`
   - `用户已被禁用` → `map_users.status=0`


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
| `DB_HOST` | string | `t0pawmmapdata-my.db.qa.pab.com.cn` | ✅ | DBA 提供 |
| `DB_PORT` | int | `3306` | ✅ | 标准 MySQL 端口 |
| `DB_USER` | string | `deployop` | ✅ | 最高权限账号（首期跑通） |
| `DB_PASSWORD` | string | `j3eKJSbX29e3` | ✅ | 首期明文配置，生产建议走密钥管理 |
| `DB_NAME` | string | `pawmmapdata` | ✅ | DBA 已建库 |
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
| `SSO_LOGIN_URL` | string | `http://wm.paic.com.cn/lckj/pawm-uc/account_login.html` | ✅ | 门户登录页（浏览器跳转），dev/fat 走 `wm.dev.paic` / `wm.stg.paic` |
| `SSO_VALIDATE_URL` | string | `http://pawm-pfp-83022-auth-gateway.pab.com.cn/wmuc/loginServer/loginValidateToken` | ✅ | GET 请求，URL 带 `?tokenId=xxx`，返回 `{"data":{"userId","userName","realName","mailAddr"}}`；dev/fat 地址见 4.3 |
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
| `/`（带 `?ssoTokenId=`） | GET | auth/sso | ✓ | — | ✓ | — | — | — | 门户回调挂在根路径，唯一调用 SSO 校验接口的入口；不带 `ssoTokenId` 时返回欢迎页 |
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
| 出向 | MAP 应用容器（平台出口） | TDSQL VIP | TCP/3306 | 数据库连接 |
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

- [ ] `config.json` 已就绪（占位模板，敏感字段留空）
- [ ] `APP_ENV=production`、`DEBUG=false`
- [ ] `SECRET_KEY` 已通过平台密钥管理注入 `openssl rand -hex 32` 强随机值
- [ ] `CORS_ORIGINS` 已改为前端实际域名（非 `*`）
- [ ] `SSO_LOGIN_URL` / `SSO_VALIDATE_URL` / `SSO_LOGIN_REDIRECT_URL` 已按环境录入
- [ ] 数据库 6 项 (`DB_*`) 已填生产值，密码走平台密钥管理
- [ ] `PORTFOLIO_SYS_URL` / `RISK_SYS_URL`：已对接的填地址，暂未对接的留空（走 Mock）

### 8.3 基础设施联通

- [ ] `nc -zv` 验证 DB / Redis / SSO 校验接口 端口可达
- [ ] `run.sh` 首次启动自动建库 + 建表；`SHOW TABLES` 返回 8 张表
- [ ] 门户白名单已登记**我方根 URL** `https://<map 对外域名>/`

### 8.4 服务自检

- [ ] 平台状态 = "运行中"，副本数全部就绪、近期无重启
- [ ] 日志无 ERROR；可见 `RocketMQ consumer worker started (sdk=False)`
- [ ] `curl http://127.0.0.1:8000/health` → `{"status":"ok","env":"production"}`
- [ ] 对外域名 `https://<域名>/health` → 同上（验证 Ingress 链路）
- [ ] 浏览器全链路：访问 → 跳门户 → 登录 → 跳回 → Cookie 已下发 → 首屏正常
- [ ] 未带 Cookie 调 `/api/v1/auth/me` → 必须 401

### 8.5 运维基础

- [ ] 日志接公司日志平台（建议 `--log-config /etc/map/logging.json` 输出 JSON）
- [ ] 平台健康检查已指向 `GET /health`，并验证过实例异常时平台会自动重建
- [ ] 定时备份 `pawmmapdata`（DBA 侧）
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
  "DB_HOST": "t0pawmmapdata-my.db.qa.pab.com.cn",
  "DB_PORT": 3306,
  "DB_USER": "deployop",
  "DB_PASSWORD": "j3eKJSbX29e3",
  "DB_NAME": "pawmmapdata",
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

  "SSO_LOGIN_URL": "http://wm.paic.com.cn/lckj/pawm-uc/account_login.html",
  "SSO_VALIDATE_URL": "http://pawm-pfp-83022-auth-gateway.pab.com.cn/wmuc/loginServer/loginValidateToken",
  "SSO_LOGIN_REDIRECT_URL": "https://map.intranet.company.com/",

  "PORTFOLIO_SYS_URL": "http://portfolio-sys.intranet.company.com",
  "RISK_SYS_URL": "http://risk-sys.intranet.company.com",

  "EXTERNAL_HTTP_TIMEOUT": 10.0,
  "EXTERNAL_HTTP_RETRIES": 3
}
```

