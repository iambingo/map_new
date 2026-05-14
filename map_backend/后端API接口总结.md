# MAP 后端接口总结

> 生成日期: 2026-05-06
> 后端框架: FastAPI (Python 3.10+)
> 前端框架: Vue 3 + Vite + TypeScript + Element Plus

---

## 一、接口规范

### 1.1 基础信息

| 项目 | 值 |
|------|-----|
| 基础路径 | `/api` |
| API 前缀 | `/api/v1` |
| 自动文档 | `/docs` (Swagger UI), `/redoc` (ReDoc) |
| 健康检查 | `GET /health` |

### 1.2 认证机制

采用 **公司 SSO + JWT** 双模式：

- **SSO 登录**: 用户访问 SSO → 回调 `/auth/sso-callback?ssoTokenId=xxx` → 后端验证 token → 签发 JWT → 设置 HttpOnly Cookie `mapToken` → 重定向到前端
- **接口鉴权**: 支持两种方式（优先级从高到低）
  1. `Authorization: Bearer <jwt>` 请求头
  2. `mapToken` HttpOnly Cookie（浏览器自动携带）
- **开发模式**: `DEBUG=true` 时跳过认证，fallback `user_id=1`

### 1.3 响应格式

**成功响应**: 多数端点返回 `{"data": ...}` 包裹，部分直接返回 Pydantic 模型 JSON。

**错误响应** (统一格式):
```json
{
  "success": false,
  "error_code": 10001,
  "message": "Resource not found",
  "detail": null
}
```

**错误码范围**:
| 范围 | 类别 | 示例 |
|------|------|------|
| 10000 | 通用错误 | UNKNOWN, VALIDATION_ERROR, NOT_FOUND, PERMISSION_DENIED, UNAUTHENTICATED |
| 20000 | 外部服务 | EXTERNAL_TIMEOUT, EXTERNAL_UNAVAILABLE, EXTERNAL_BAD_RESPONSE |
| 30000 | 业务规则 | BUSINESS_RULE_VIOLATION, STALE_SNAPSHOT, TASK_ALREADY_PROCESSING |

### 1.4 数据模型公共字段

所有数据库模型继承自 `Base`，包含：
- `id` (BigInteger, 自增主键)
- `created_at` (DateTime, 自动填充)
- `updated_at` (DateTime, 自动更新)
- `is_deleted` (SmallInteger, 软删除标记)

> **架构约束**: 无物理外键，跨表关系使用逻辑 ID + 索引。

### 1.5 CORS 配置

开发环境 `CORS_ORIGINS=*`，生产环境应配置具体域名。Credentials 模式启用。

---

## 二、已实现接口清单

### 2.1 认证模块 (`/api/v1/auth`)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/auth/me` | 获取当前用户信息 (从 JWT 解析) | 需要 JWT |
| GET | `/auth/sso-callback` | SSO 回调：验证 token、签发 JWT、设置 Cookie、重定向 | 无 |

### 2.2 投委会模块 (`/api/v1/committee`)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/committee/meetings` | 会议列表（可按状态筛选） | JWT/Cookie |
| POST | `/api/v1/committee/meetings` | 创建会议（DRAFT 状态），返回 201 | JWT/Cookie |
| POST | `/api/v1/committee/meetings/{meeting_id}/submit-vote` | 提交/覆盖投票（幂等，DRAFT→VOTING 自动转换） | JWT/Cookie |
| POST | `/api/v1/committee/meetings/{meeting_id}/publish` | 触发投票聚合并发布决议（不可逆） | JWT/Cookie |
| GET | `/api/v1/committee/page-context` | 只读上下文：最新决议 + 会议元数据 + 投票摘要 | JWT/Cookie |

### 2.3 混合投委会问卷 (`/api/v1/committee/mixed`)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/committee/mixed/submit` | 提交/覆盖资配观点（幂等：session_code + submitter_id） | 需要 JWT |
| GET | `/api/v1/committee/mixed/sessions` | 列出某 session 的所有提交（管理员视角，含评分明细） | JWT/Cookie |
| GET | `/api/v1/committee/mixed/sessions/history` | 历史会期列表 + 聚合评分统计 | JWT/Cookie |
| POST | `/api/v1/committee/mixed/remind` | 向未提交的委员发送催办通知 | 需要 JWT |

### 2.4 工作空间/门户 (`/api/v1/workspace`)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/workspace/portal-snapshot` | 门户首页完整快照（TAA 指引 + 持仓 + 偏差分析 + 导航卡片），Redis 缓存 + 优雅降级 | JWT/Cookie |

### 2.5 编排器 (`/api/v1/orchestrator`)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/orchestrator/commands` | 注册并派发跨域命令（202 Accepted），支持 MQ 异步或同步 | 需要 JWT |
| GET | `/api/v1/orchestrator/commands/{task_id}` | 查询命令执行状态（前端轮询用） | 需要 JWT |

已注册命令类型:
- `SUBMIT_SAA_FOR_APPROVAL`
- `PUBLISH_SAA_RESULT`
- `TRIGGER_PORTFOLIO_REBALANCE`
- `SYNC_PORTFOLIO_SNAPSHOT`
- `NOTIFY_IC_RESOLUTION_PUBLISHED`
- `REQUEST_RESEARCH_REPORT`

### 2.6 资产配置 (`/api/v1/asset-allocation`)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/asset-allocation/asset-classes` | 资产类别配置列表 | JWT/Cookie |
| GET | `/api/v1/asset-allocation/drafts` | 用户的 SAA 草稿列表（可按状态筛选） | JWT/Cookie |
| GET | `/api/v1/asset-allocation/drafts/{draft_id}` | 获取草稿详情 | JWT/Cookie |
| POST | `/api/v1/asset-allocation/drafts/calculate` | 执行 SAA 计算并保存草稿 | JWT/Cookie |
| POST | `/api/v1/asset-allocation/drafts/{draft_id}/submit` | 提交草稿待审批 | JWT/Cookie |
| POST | `/api/v1/asset-allocation/drafts/{draft_id}/approve` | 审批通过草稿 | 需要 JWT |
| POST | `/api/v1/asset-allocation/drafts/{draft_id}/reject` | 驳回草稿（含驳回理由） | 需要 JWT |

### 2.7 消息中心 (`/api/v1/messages`)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/messages/events/stream` | SSE 实时事件流（text/event-stream），25s 心跳 | JWT/Cookie |
| POST | `/api/v1/messages/webhooks/signal` | 接收外部系统原始信号（202 Accepted） | 无 |

### 2.8 健康检查

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/health` | 系统健康检查 | 无 |

---

## 三、数据库模型 (8 张表)

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `map_users` | 用户账户 | portal_user_id, username |
| `ic_meetings` | 投委会会议 | meeting_code, title, type, status (DRAFT/VOTING/PUBLISHED) |
| `ic_vote_records` | 投票记录 | meeting_id, user_id, choice_items (JSON), numeric_items (JSON) |
| `ic_resolutions` | 已发布决议 | meeting_id, aggregated_taa (JSON), ai_minutes |
| `ic_mixed_questionnaire_submissions` | 混合问卷提交 | session_code, submitter_id, questionnaire_json (JSON) |
| `saa_drafts` | SAA 草稿版本 | user_id, status, version, calculation_result (JSON) |
| `asset_class_configs` | 资产类别配置 | asset_class, expected_return, volatility, weight_min, weight_max |
| `pending_commands` | 跨域命令注册 | command_type, unique_key, status, task_id |

---

## 四、前后端打通情况

### 4.1 已打通的接口

| 后端接口 | 前端调用位置 | 调用方式 | 状态 |
|----------|-------------|----------|------|
| `GET /v1/workspace/portal-snapshot` | `demoStore.ts:fetchMeetingResolution()`, `demoStore.ts:fetchCommitteePageData()` | axios GET + role 参数 | **已对接** |
| `GET /v1/committee/page-context` | `demoStore.ts:fetchCommitteePageData()` | axios GET | **已对接** |
| `GET /v1/committee/meetings` | `CommitteeView.vue:loadMeetings()` | axios GET | **已对接** |
| `POST /v1/committee/meetings` | `CommitteeView.vue:quickCreateMeeting()` | axios POST | **已对接**（含唯一键冲突重试） |
| `GET /v1/committee/mixed/sessions` | `CommitteeView.vue:loadMixedSubmissions()` | axios GET | **已对接** |
| `GET /v1/committee/mixed/sessions/history` | `CommitteeView.vue:loadHistoryVotes()` | axios GET + limit 参数 | **已对接** |
| `POST /v1/committee/mixed/remind` | `CommitteeView.vue:handleUrgentRemindApi()` | axios POST | **已对接** |
| `POST /v1/committee/meetings/{id}/submit-vote` | `CommitteeView.vue` 投票提交 | axios POST | **已对接** |

### 4.2 后端已实现但前端未调用的接口

| 后端接口 | 说明 | 前端状态 |
|----------|------|----------|
| `GET /api/v1/auth/me` | 获取当前用户信息 | **未对接**（前端使用 hardcoded JWT + role 切换） |
| `POST /api/v1/committee/mixed/submit` | 提交混合问卷 | **未对接**（前端有 UI 但未调用此接口） |
| `POST /api/v1/committee/meetings/{id}/publish` | 发布决议 | **未对接** |
| `GET /api/v1/asset-allocation/*` | 全部 SAA 相关接口 | **未对接**（前端有 SAASimulator.vue 组件但未调 API） |
| `POST /api/v1/orchestrator/commands` | 命令派发 | **未对接** |
| `GET /api/v1/orchestrator/commands/{task_id}` | 命令状态查询 | **未对接** |
| `GET /api/v1/messages/events/stream` | SSE 实时推送 | **未对接** |
| `POST /api/v1/messages/webhooks/signal` | 接收外部信号 | **未对接** |

### 4.3 前端存在但后端暂无对应接口的功能

| 前端功能 | 说明 |
|----------|------|
| 持仓数据加载/更新 | 前端使用 Mock 数据，标注 TODO "待产品业绩系统 API" |
| 策略排行 | 前端使用 Mock 数据，标注 TODO "待策略排行 API" |
| 模型输出（回测/风控） | 前端使用 Mock 数据，标注 TODO "待模型输出 API" |
| 用户目录 | 前端硬编码 MEMBERS_DATA，标注 TODO "待用户目录 API" |
| 外部系统对接 (Portfolio/Risk) | 后端有 adapter 骨架 (Mock 模式)，未启用真实 HTTP 调用 |

### 4.4 前端认证现状

前端当前使用 **hardcoded JWT** (`HARDCODED_DEV_BEARER`):
- 文件: `src/api/request.ts`
- Token 对应 `sub=1`, 使用当前 `.env` 的 `SECRET_KEY` 生成
- 支持通过 `localStorage.map_access_token` 覆盖
- **注意**: 此方式绕过了 SSO 流程，仅适用于开发联调

---

## 五、前端架构概要

| 项目 | 值 |
|------|-----|
| 框架 | Vue 3 + TypeScript |
| 构建 | Vite |
| UI 库 | Element Plus |
| 状态管理 | Vue Reactivity API (`ref`, `computed`, `reactive`) |
| HTTP 客户端 | Axios (自定义实例 `http`) |
| API 基础路径 | `VITE_API_BASE_URL` 环境变量（默认 `/api`） |
| 离线模式 | `VITE_COMMITTEE_OFFLINE_MOCK=true` 可跳过 API 请求 |
| 主要组件 | CommitteeView, FiccCommitteeView, SAASimulator, MapPortal, ExecutiveDashboard, BatchSimulator, FactorWorkshop, ViewpointWorkshop, ModelCenterView, SettingsView |

---

## 六、中间件与基础设施

| 组件 | 状态 | 说明 |
|------|------|------|
| TDSQL (MySQL 8 兼容) | 已接入 | 端口 5400，async aiomysql 驱动 |
| SQLite | 可用 | `MAP_USE_SQLITE=true` 开发 fallback |
| Redis | 已接入 | 异步客户端，用于 portal-snapshot 缓存 |
| RocketMQ | 骨架模式 | producer + consumer 已注册，stub 状态 |
| Alembic | 已配置 | 数据库迁移工具 |
| Docker Compose | 可用 | 含 TDSQL + Redis + RocketMQ 初始化脚本 |
