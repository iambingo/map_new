# MAP 后端接口总结

> 最后修订: 2026-05-08（v1.9.5 审计同步，新增 Tab 结构变更与新 Mock 清单）
> 后端框架: FastAPI (Python 3.10+)
> 前端框架: Vue 3 + Vite + TypeScript + Element Plus

---

## 一、接口规范

### 1.1 基础信息

| 项目 | 值 |
|------|-----|
| 服务基础路径 | `/api` |
| API 前缀 | `/api/v1` |
| 自动文档 | `/docs` (Swagger UI), `/redoc` (ReDoc) |
| 健康检查 | `GET /health` |

> **路径约定（重要）**: 后端路由以 `/api/v1/...` 注册。前端 Axios `baseURL = /api`，故前端代码中的路径一律写 `/v1/...`（不含 `/api`）。本文档接口清单统一使用**完整路径** `/api/v1/...`，以避免双轨并行引起歧义。

### 1.2 命名规范（强制约束）

**前后端数据交互统一采用 `snake_case`（下划线小写）命名规范。**

- 后端所有 JSON 字段、Query 参数、Path 参数均使用 `snake_case`。
- 前端本地状态使用 `camelCase`，在发送请求前须自行映射为 `snake_case`，接收响应后须自行反向映射。
- 枚举值（如 `type`、`status`）统一使用**全小写**（`mixed`、`ficc`、`draft`、`voting`、`published`），禁止使用 `MIXED`、`VOTING` 等大写形式传入 API。

### 1.3 认证机制

采用 **公司 SSO + JWT** 双模式：

- **SSO 登录**: 用户访问 SSO → 回调 `/auth/sso-callback?sso_token_id=xxx` → 后端验证 token → 签发 JWT → 设置 HttpOnly Cookie `mapToken` → 重定向到前端
- **接口鉴权**: 支持两种方式（优先级从高到低）
  1. `Authorization: Bearer <jwt>` 请求头
  2. `mapToken` HttpOnly Cookie（浏览器自动携带）
- **开发模式**: `DEBUG=true` 时跳过认证，fallback `user_id=1`

### 1.4 响应格式

**成功响应**: 多数端点返回 `{"data": ...}` 包裹，部分端点（GET 列表/详情）直接返回 Pydantic 模型 JSON。具体见各端点定义。

**错误响应**（统一格式）:
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

### 1.5 数据模型公共字段

所有数据库模型继承自 `Base`，包含：
- `id` (BigInteger, 自增主键)
- `created_at` (DateTime, 自动填充)
- `updated_at` (DateTime, 自动更新)
- `is_deleted` (SmallInteger, 软删除标记，0=正常，1=已删除)

> **架构约束**: 无物理外键，跨表关系使用逻辑 ID + 索引。

### 1.6 CORS 配置

开发环境 `CORS_ORIGINS=*`，生产环境应配置具体域名。Credentials 模式启用。

---

## 二、接口清单总览

### 2.1 认证模块 (`/api/v1/auth`)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/auth/me` | 获取当前用户信息（从 JWT 解析） | 需要 JWT |
| GET | `/auth/sso-callback` | SSO 回调：验证 token、签发 JWT、设置 Cookie、重定向 | 无 |

### 2.2 投委会模块 (`/api/v1/committee`)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/committee/meetings` | 会议列表（支持 `?type=` 筛选） | JWT/Cookie |
| POST | `/api/v1/committee/meetings` | 创建会议（`draft` 状态），返回 201 | JWT/Cookie |
| DELETE | `/api/v1/committee/meetings/{meeting_id}` | 软删除会议（`is_deleted=1`） | JWT/Cookie |
| POST | `/api/v1/committee/meetings/{meeting_id}/submit-vote` | 提交/覆盖投票（幂等） | JWT/Cookie |
| POST | `/api/v1/committee/meetings/{meeting_id}/publish` | 触发聚合并发布决议（不可逆） | JWT/Cookie |
| POST | `/api/v1/committee/meetings/{meeting_id}/resolution` | 保存主任委员最终资配决议 | JWT/Cookie |
| GET | `/api/v1/committee/page-context` | 只读上下文：最新决议 + 会议元数据 + 投票摘要 | JWT/Cookie |

### 2.3 混合投委会问卷 (`/api/v1/committee/mixed`)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/committee/mixed/submit` | 提交/覆盖资配观点问卷（幂等：session_code + submitter_id） | 需要 JWT |
| GET | `/api/v1/committee/mixed/sessions` | 列出指定会期的所有提交（含评分明细） | JWT/Cookie |
| GET | `/api/v1/committee/mixed/sessions/history` | 历史会期列表 + 聚合评分统计 | JWT/Cookie |
| POST | `/api/v1/committee/mixed/remind` | 向未提交的委员发送催办通知 | 需要 JWT |

### 2.4 工作空间/门户 (`/api/v1/workspace`)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/workspace/portal-snapshot` | 门户首页完整快照（TAA 指引 + 持仓 + 偏差分析 + 导航卡片），Redis 缓存 + 优雅降级 | JWT/Cookie |

### 2.5 编排器 (`/api/v1/orchestrator`)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| POST | `/api/v1/orchestrator/commands` | 注册并派发跨域命令（202 Accepted） | 需要 JWT |
| GET | `/api/v1/orchestrator/commands/{task_id}` | 查询命令执行状态（前端轮询用） | 需要 JWT |

### 2.6 资产配置 (`/api/v1/asset-allocation`)

| 方法 | 路径 | 说明 | 认证 |
|------|------|------|------|
| GET | `/api/v1/asset-allocation/asset-classes` | 资产类别配置列表 | JWT/Cookie |
| GET | `/api/v1/asset-allocation/drafts` | 用户的 SAA 草稿列表 | JWT/Cookie |
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

## 三、关键接口完整 Schema

> 以下所有字段类型标注以 **后端 Pydantic DTO** 视角为准，前端 TypeScript 类型在注释中标明。

---

### 3.1 GET `/api/v1/workspace/portal-snapshot`

**请求参数**:

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `role` | query | string | 是 | 角色枚举，见下表。后端**必须**按此值过滤返回数据的权限范围。 |

**`role` 枚举值与角色映射（前端 `ROLE_QUERY` 字典，目标映射 / 待修正）**:

> **⚠️ 当前前端代码 (`demoStore.ts:1123`) 仍使用旧映射**：`班子→ADMIN`、`部门长→COMMITTEE_MEMBER`、`投管→PM`。
> 下表为**目标映射**，需前端同步修改 `ROLE_QUERY` 后方可生效。后端应以下表为准实现。

| 前端角色（中文） | `role` 目标传参值 | 当前代码实际传参 | 说明 |
|----------------|------------------|----------------|------|
| 班子 | `LEADERSHIP` | `ADMIN` | ⚠️ 命名冲突，需改为 `LEADERSHIP` |
| 部门长 | `DEPT_HEAD` | `COMMITTEE_MEMBER` | ⚠️ 与委员重复，需改为 `DEPT_HEAD` |
| 投资经理 | `PM` | `PM` | |
| 投资助理 | `ANALYST` | `ANALYST` | |
| 投管 | `PORTFOLIO_MANAGER` | `PM` | ⚠️ 与投资经理重复，需改为 `PORTFOLIO_MANAGER` |
| 混合投资委员会秘书 | `COMMITTEE_SECRETARY` | `COMMITTEE_SECRETARY` | |
| 混合投资委员会委员 | `COMMITTEE_MEMBER` | `COMMITTEE_MEMBER` | |
| 混合投资委员会主任委员 | `COMMITTEE_CHAIR` | `COMMITTEE_CHAIR` | |
| FICC投资委员会秘书 | `FICC_SECRETARY` | `FICC_SECRETARY` | |
| FICC投资委员会委员 | `FICC_MEMBER` | `FICC_MEMBER` | |
| FICC投资委员会主任委员 | `FICC_CHAIR` | `FICC_CHAIR` | |

**响应体**:

```typescript
// HTTP 200 — 直接返回 JSON 对象（无 data 包裹）
{
  snapshot_at: string;          // ISO 8601 datetime, e.g. "2026-04-15T14:00:00+08:00"
  is_stale: boolean;            // true = 缓存陈旧，需重建
  stale_reason: string | null;  // 陈旧原因描述，is_stale=false 时为 null

  taa_guidance: {
    source_resolution: {
      resolution_id: number | null;
      meeting_id: number | null;
      published_at: string | null;  // ISO 8601
    } | null;

    // key 枚举："equity_view" | "bond_view" | "commodity_view" | "cash_view"
    choice_results: {
      [view_key: string]: {
        winner: "overweight" | "neutral" | "underweight";
        vote_counts: {
          [level: string]: number;  // e.g. {"overweight": 3, "neutral": 2, "underweight": 1}
        };
      };
    };

    numeric_results: {
      [asset_name: string]: {
        [metric: string]: number | string | null;
      };
    };

    published_at: string | null;  // ISO 8601
  };

  positions: {
    [asset_class: string]: unknown;
  } | null;

  deviation_analysis: {
    [key: string]: unknown;
  };

  rebalance_urgency: {
    level: string;   // e.g. "low" | "medium" | "high"
    reason: string;
  };

  navigation_tiles: Array<{
    [key: string]: unknown;
  }>;
}
```

**`winner` → 前端中文映射（`winnerToCN`）**:
| 后端值 | 前端显示 |
|--------|----------|
| `overweight` | 乐观 |
| `neutral` | 中性 |
| `underweight` | 谨慎 |

---

### 3.2 GET `/api/v1/committee/page-context`

**请求参数**:

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `committee_type` | query | string | 否 | `"mixed"` 或 `"ficc"`，默认 `"mixed"`。后端按此值返回对应投委会类型的最新会议 + 决议上下文 |

**响应体**:

```typescript
// HTTP 200 — 直接返回 JSON 对象
{
  meeting: {
    id: number;
    meeting_code: string;         // e.g. "IC-2026-Q2-15142537"
    title: string;
    type: "mixed" | "ficc";       // 小写，前端映射到中文显示
    status: "draft" | "voting" | "published";  // 前端映射：draft→筹备中, voting→进行中, published→已结束
    scheduled_at: string | null;  // ISO 8601
    created_by: number;           // user_id
    created_at: string;           // ISO 8601
    updated_at: string;           // ISO 8601
  } | null;

  resolution: {
    id: number;
    meeting_id: number;
    aggregated_taa: {
      // 结构与 portal-snapshot.taa_guidance 的 choice_results 完全一致，
      // 供 portal-snapshot 无数据时作为 fallback
      choice_results?: {
        [view_key: string]: {
          winner: "overweight" | "neutral" | "underweight";
          vote_counts: { [level: string]: number };
        };
      };
      [key: string]: unknown;
    };
    ai_minutes: string | null;    // AI 生成的会议纪要 Markdown 文本
    published_at: string | null;  // ISO 8601
    published_by: number | null;  // user_id
    created_at: string;           // ISO 8601
  } | null;

  votes: Array<{
    user_id: number;
    submitted_at: string | null;  // ISO 8601
  }>;
}
```

**前端使用逻辑**:
- `portal-snapshot` 与 `page-context` 通过 `Promise.allSettled` 并行请求，互不阻塞。
- 优先用 `portal-snapshot.taa_guidance.choice_results` 渲染决议表；若为空，则 fallback 到 `resolution.aggregated_taa.choice_results`。

---

### 3.3 GET `/api/v1/committee/meetings`

**请求参数**:

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `type` | query | string | 否 | `"mixed"` 或 `"ficc"`，不传返回全部类型 |
| `status` | query | string | 否 | `"draft"` / `"voting"` / `"published"`，不传返回全部状态 |

**响应体**:

```typescript
// HTTP 200 — 返回数组（直接，无 data 包裹）
Array<{
  id: number;
  meeting_code: string;
  title: string;
  type: "mixed" | "ficc";
  status: "draft" | "voting" | "published";
  scheduled_at: string | null;  // ISO 8601
  created_by: number;
  created_at: string;           // ISO 8601
  updated_at: string;           // ISO 8601
}>
```

---

### 3.4 POST `/api/v1/committee/meetings`

**请求体**:

```typescript
{
  meeting_code: string;   // 前端生成，格式 "IC-{year}-{quarter}-{ddHHMMSSrr}"
                          // e.g. "IC-2026-Q2-1514253741"
                          // 后端须有 UNIQUE 约束；冲突时返回 HTTP 409
  title: string;          // e.g. "混合投资委员会 2026 Q2 配置决策会议"
  type: "mixed" | "ficc"; // 必须小写
  scheduled_at?: string;  // ISO 8601，可选
}
```

**响应**: HTTP 201，返回创建的会议对象（同 §3.3 的数组元素结构）。

**冲突处理**: `meeting_code` 唯一键冲突时返回 HTTP 409，前端会自动重试最多 3 次。

---

### 3.5 DELETE `/api/v1/committee/meetings/{meeting_id}`

**Path 参数**: `meeting_id` (integer)

**行为**: 软删除，将 `is_deleted` 置为 1，不物理删除。

**权限约束**: 仅会议创建者或 `COMMITTEE_SECRETARY` / `FICC_SECRETARY` 角色可执行。

**响应**: HTTP 204 No Content。失败时返回标准错误格式。

---

### 3.6 POST `/api/v1/committee/meetings/{meeting_id}/submit-vote`

这是**两套投委会共用的核心投票端点**。通过 `committee_type` 字段区分处理逻辑。

**Path 参数**: `meeting_id` (integer)

**请求体（统一格式，`snake_case`）**:

```typescript
{
  // ── 必填：投委会类型鉴别 ──────────────────────────────────────────────
  committee_type: "mixed" | "ficc";

  // ── 必填：投票维度（FICC 专用季度模式） ───────────────────────────────
  vote_dimension: "monthly" | "quarterly";  // mixed 固定传 "monthly"

  // ── 混合投委会资产评分（Section A）───────────────────────────────────
  // key = 细分策略名（见 §五.1 资产配置字典），value = 1~5 整数档位分数
  // 混合投委会月度 6 项：红利、偏股混、恒生科技、黄金、利率(10Y)、利率(30Y)
  section_a?: {
    [asset_name: string]: number;  // integer, 1~5
  };

  // ── 创新高预判（Section B）────────────────────────────────────────────
  // key = 细分策略名，value = 是否预判该资产能创新高
  section_b?: {
    [asset_name: string]: boolean;
  };

  // ── 重点资产标记（Section C）──────────────────────────────────────────
  // 本次重点关注的资产名称列表（来自 FORM_SECTION_C 复选框）
  section_c?: string[];  // e.g. ["利率债", "黄金", "REITs"]

  // ── 委员综合市场观点（必填，非空字符串时才允许提交） ──────────────────
  core_view?: string;

  // ── 风险提示标记 ──────────────────────────────────────────────────────
  risk_flag?: boolean;  // 注意：类型为 boolean，不是字符串

  // ── FICC 专有扩展字段（仓位/久期/含权，vote_dimension=monthly 时有效）
  // 存入 ic_vote_records.numeric_items，key 使用固定名称
  ficc_position_pct?: number;  // 稳定资产仓位比例，0~100 整数
  ficc_duration_pct?: number;  // 久期使用率，0~100 整数
  ficc_equity_pct?: number;    // 穿透含权率，0~100 整数

  // ── 代填模式字段（秘书为委员代填时携带） ─────────────────────────────
  target_member_id?: number;        // 被代填委员的 user_id（对应 map_users.id）
  is_proxy?: boolean;              // true = 代填提交
  proxy_submitter_role?: string;   // 代填人角色，如 "COMMITTEE_SECRETARY"
}
```

**后端存储映射**（`ic_vote_records` 表）:

| 请求字段 | 存储字段 | 说明 |
|---------|---------|------|
| `section_a` | `choice_items.section_a` (JSON object) | 嵌套存入，key 为资产名，value 为 1~5 整数 |
| `section_b` | `choice_items.section_b` (JSON object) | 嵌套存入，key 为资产名，value 为 boolean |
| `section_c` | `choice_items.section_c` (JSON array) | 嵌套存入 |
| `core_view` | `choice_items.core_view` (string) | 嵌套存入 |
| `risk_flag` | `choice_items.risk_flag` (boolean) | 嵌套存入 |
| `ficc_position_pct` | `numeric_items.ficc_position_pct` (number) | |
| `ficc_duration_pct` | `numeric_items.ficc_duration_pct` (number) | |
| `ficc_equity_pct` | `numeric_items.ficc_equity_pct` (number) | |

**`choice_items` 落库示例**（完整请求 → 存储形态）:

前端请求体:
```json
{
  "committee_type": "mixed",
  "vote_dimension": "monthly",
  "section_a": { "红利": 4, "偏股混": 3, "恒生科技": 5, "黄金": 4, "利率(10Y)": 3, "利率(30Y)": 2 },
  "section_b": { "红利": true, "恒生科技": true, "黄金": false },
  "section_c": ["利率债", "黄金"],
  "core_view": "权益偏乐观，固收短久期",
  "risk_flag": false
}
```

后端 `choice_items` 列落库 JSON:
```json
{
  "section_a": { "红利": 4, "偏股混": 3, "恒生科技": 5, "黄金": 4, "利率(10Y)": 3, "利率(30Y)": 2 },
  "section_b": { "红利": true, "恒生科技": true, "黄金": false },
  "section_c": ["利率债", "黄金"],
  "core_view": "权益偏乐观，固收短久期",
  "risk_flag": false
}
```

> **关键约束**: `choice_items` 为**嵌套结构**（非扁平），每个段有独立的 key。后端读取时按 `section_a`/`section_b`/`section_c` 分别取值。

**响应**: HTTP 200，返回提交记录的摘要：
```typescript
{
  vote_id: number;
  meeting_id: number;
  user_id: number;
  submitted_at: string;  // ISO 8601
}
```

**幂等规则**: 同一 `meeting_id + user_id` 重复提交时，覆盖旧记录（UPSERT）。

---

### 3.7 POST `/api/v1/committee/meetings/{meeting_id}/publish`

**方法**: `POST`（非 GET，此处为最终确认）

**Path 参数**: `meeting_id` (integer)

**请求体**: 空（无需 body）。

**行为**: 触发投票聚合计算 + 生成 AI 纪要 + 将会议状态改为 `published`。**操作不可逆**。

**响应体** (HTTP 200):

```typescript
{
  resolution_id: number;
  meeting_id: number;
  aggregated_taa: {
    choice_results: {
      [view_key: string]: {  // "equity_view" | "bond_view" | "commodity_view" | "cash_view"
        winner: "overweight" | "neutral" | "underweight";
        vote_counts: { [level: string]: number };
      };
    };
    [key: string]: unknown;
  };
  ai_minutes: string | null;   // AI 生成的 Markdown 会议纪要
  published_at: string;        // ISO 8601
  published_by: number;        // user_id
}
```

---

### 3.8 POST `/api/v1/committee/meetings/{meeting_id}/resolution`

> **新增端点**：用于持久化主任委员在 Step 3 确认的最终部门资配决议。此前该数据仅存于前端本地状态，刷新即丢失。

**Path 参数**: `meeting_id` (integer)

**请求体**:

```typescript
{
  // 固收久期档位（高 = 长久期 3-7Y，中 = 中久期 1-3Y，低 = 短久期 0-1Y）
  bond_grade: "高" | "中" | "低";
  bond_duration: string;   // e.g. "3-7年"，前端由 BOND_GRADE_DURATION 映射计算

  // 权益档位（1=谨慎, 2=中性偏谨慎, 3=中性, 4=中性偏乐观, 5=乐观）
  equity_grade: number;    // integer, 1~5
  equity_grade_label: string;  // e.g. "中性偏乐观"

  // 权益明细分配（各项加总应为 100）
  equity_mix: {
    red_li: number;   // 红利 %
    cheng_zhang: number;  // 成长 %
    jia_zhi: number;  // 价值 %
  };

  // 另类资产备注
  alt_notes: string;

  // 三类产品指引
  products: Array<{
    product_id: "low" | "mid" | "hybrid";
    product_name: string;   // e.g. "固收+中低波"
    bond_grade: "高" | "中" | "低";  // 该产品类型的固收久期
    bond_pct: number;       // 固收仓位 %
    equity_pct: number;     // 权益总仓位 %
    equity_sub: {
      red_li: number;       // 红利 %
      hk: number;           // 港股 %
      other_equity: number; // 其他权益 %
      reits: number;        // REITs %
      gold: number;         // 黄金 %
    };
    alt_pct: number;        // 另类 %
    liquidity_pct: number;  // 流动性 %
  }>;
}
```

**响应**: HTTP 201，返回创建的决议记录（含 `id`、`created_at`）。

---

### 3.9 GET `/api/v1/committee/mixed/sessions`

**请求参数**:

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `session_code` | query | string | 否 | 会期编号，如 `"IC2026Q2"`。不传则返回**最新进行中会期**的提交。 |
| `committee_type` | query | string | 否 | `"mixed"` 或 `"ficc"`，默认 `"mixed"` |

**响应体**:

```typescript
// HTTP 200 — 直接返回 JSON 对象
{
  session_code: string;   // 本次返回的会期编号

  submissions: Array<{
    submitter_id: number;            // 对应 map_users.id
    submitted_at: string;            // ISO 8601

    // ── questionnaire_json 为完整三段式结构 ──────────────────────────────
    questionnaire_json: {
      // Section A: 资产评分，key=细分策略名，value=1~5 整数档位分数
      section_a: {
        [asset_name: string]: number;  // integer, 1~5
      };

      // Section B: 创新高预判，key=细分策略名，value=boolean
      section_b: {
        [asset_name: string]: boolean;
      };

      // Section C: 重点资产列表（字符串数组）
      section_c: string[];

      // 委员综合市场观点
      core_view: string;

      // 风险提示标记
      risk_flag: boolean;
    };
  }>;
}
```

> **关键约束**: `questionnaire_json.section_a` 的值是 **1~5 的整数档位分数**，不是中文档位名称字符串（`"中性偏乐观"` 等）。前端渲染时通过 `SCORE_LABELS` 字典转换。

---

### 3.10 GET `/api/v1/committee/mixed/sessions/history`

**请求参数**:

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| `limit` | query | integer | 否 | 返回条数上限，前端默认传 `10` |
| `committee_type` | query | string | 否 | `"mixed"` 或 `"ficc"`，默认 `"mixed"` |
| `vote_dimension` | query | string | 否 | `"monthly"` 或 `"quarterly"`，默认 `"monthly"` |

**响应体**:

```typescript
// HTTP 200 — 直接返回 JSON 对象
{
  sessions: Array<{
    session_code: string;     // e.g. "IC2026Q2"
    submitted_count: number;  // 已提交委员数
    scores: {
      // key = 细分策略名
      [asset_name: string]: {
        avg: number;    // 加权均值，1~5，保留 2 位小数
        max: number;    // 最高分，integer 1~5
        min: number;    // 最低分，integer 1~5
        count: number;  // 参与投票人数
      };
    };
  }>;
}
```

---

### 3.11 POST `/api/v1/committee/mixed/submit`

> 面向**混合问卷**的独立提交端点，与 `submit-vote`（会议级别）并存。按 `session_code + submitter_id` 幂等。

**请求体**:

```typescript
{
  session_code: string;  // 会期编号，e.g. "IC2026Q2"

  // questionnaire_json 结构与 §3.9 响应中完全一致（三段式）
  questionnaire_json: {
    section_a: { [asset_name: string]: number };   // 1~5 整数
    section_b: { [asset_name: string]: boolean };
    section_c: string[];
    core_view: string;
    risk_flag: boolean;
  };
}
```

**响应**: HTTP 201，返回提交记录（含 `id`、`session_code`、`submitter_id`、`submitted_at`）。

---

### 3.12 POST `/api/v1/committee/mixed/remind`

**请求体**:

```typescript
{
  member_name: string;   // 委员姓名，用于通知内容
  member_id?: number;    // 委员 user_id，可选，用于精准推送
}
```

**响应**: HTTP 200，`{ "success": true, "message": "催办通知已发送" }`。

---

## 四、前端视图接口对齐清单

> **状态定义（三态分类）**:
> - ✅ **已按契约对接** — 请求路径、参数、payload 均符合本文档 Schema
> - ⚠️ **已调用但待修复** — 已发送 HTTP 请求，但 payload/参数与文档不一致，联调时会报错
> - ❌ **待对接** — 未发送 HTTP 请求，使用本地 Mock

### 4.1 CommitteeView（混合投委会）— 接口对接状态

> **Tab 结构变更（v1.9.x）**: 原有 Step 0~4 流程已重构为 5 个 Tab 页，当前结构：
> | Tab Key | 中文标签 | Step |
> |---------|---------|------|
> | `market_macro` | 市场及产品表现回顾 | 01 |
> | `post_mortem` | 知行果复盘 | 02 |
> | `member_views` | 委员观点 | 03 |
> | `allocation` | 配置指引 | 04 |
> | `minutes` | 会议纪要 | 05 |

| 后端接口 | 前端调用函数 | 状态 | 备注 |
|----------|------------|------|------|
| `GET /api/v1/workspace/portal-snapshot` | `fetchMeetingResolution()` / `fetchCommitteePageData()` | ✅ 已按契约对接 | |
| `GET /api/v1/committee/page-context` | `fetchCommitteePageData()` | ✅ 已按契约对接 | 当前未传 `committee_type`，默认 `mixed` 可用 |
| `GET /api/v1/committee/meetings` | `loadMeetings()` | ⚠️ 已调用但待修复 | 未传 `?type=mixed`，后端返回全部类型时会混入 FICC 会议（见 B7） |
| `POST /api/v1/committee/meetings` | `quickCreateMeeting()` | ⚠️ 已调用但待修复 | `type: 'MIXED'` 大写，后端期望小写 `'mixed'`（见 B4） |
| `DELETE /api/v1/committee/meetings/{id}` | `deleteMeeting()` | ✅ 已按契约对接 | |
| `POST /api/v1/committee/meetings/{id}/submit-vote` | `submitMemberForm()` / `submitMemberFormSelf()` / `submitProxyVote()` | ⚠️ 已调用但待修复 | payload 结构不符合 §3.6（见 B1-B3） |
| `GET /api/v1/committee/mixed/sessions` | `loadMixedSubmissions()` | ✅ 已按契约对接 | |
| `GET /api/v1/committee/mixed/sessions/history` | `loadHistoryVotes()` | ✅ 已按契约对接 | |
| `POST /api/v1/committee/mixed/remind` | `handleUrgentRemindApi()` | ✅ 已按契约对接 | |
| `POST /api/v1/committee/meetings/{id}/resolution` | `handleSubmitDecision()` | ❌ 待对接 | 端点已定义（§3.8），但 `handleSubmitDecision()` 仅写本地状态，未发送 HTTP 请求（见 B8） |

### 4.2 CommitteeView — 仍使用 Mock 数据的功能（待后端 API）

| # | Mock 变量名 | 待对接 API |
|---|------------|-----------|
| M1 | `MEMBERS_DATA` / `COMMITTEE_MEMBERS` | `GET /api/v1/auth/me` + 用户目录 API（从 JWT 解析） |
| M2 | `PRODUCT_CATEGORIES` | 待产品业绩系统 API（外部系统） |
| M3/M4 | `TOP_STRATEGIES` / `BOTTOM_STRATEGIES` | 待策略排行 API（外部系统） |
| M5 | `MODEL_OUTPUTS` | 待模型输出 API（外部系统：回测/风控） |
| M6 | `PREV_PERIOD_REVIEW_MIXED` | `GET /api/v1/committee/mixed/sessions/history?limit=1`（可从历史决议聚合） |
| M7 | `CROSS_FICC_MOCK` | `GET /api/v1/committee/page-context?committee_type=ficc`（可从 FICC page-context 获取） |
| M8 | `AI_SUMMARY_POINTS` | `resolution.ai_minutes`（`POST /publish` 返回值中已包含） |
| M9 | `MACRO_INDICATORS` | 待宏观经济指标 API（外部系统：DR007、PMI、CPI 等），当前为 Tab `market_macro` 顶部卡片数据 |
| M10 | `PRODUCT_PERF_ROWS` | 待产品业绩排行 API（外部系统），当前为 Tab `market_macro` 产品表现表格数据 |

### 4.3 FiccCommitteeView（FICC 投委会）— 对接现状

> **Tab 结构变更（v1.9.x）**: FICC 视图 Tab 标签已重命名：
> | Tab Key | 旧标签 | 新标签 | Step |
> |---------|--------|--------|------|
> | `materials` | 投研观点与材料 | 委员观点 | S0 |
> | `anchors` | 市场复盘与锚点 | 市场及产品表现回顾 | S1 |
> | `decision` | 决策票台与指引 | 配置指引 | S2 |
> | `minutes` | 会议纪要与归档 | 会议纪要 | S3 |

| 后端接口 | FICC 前端状态 | 说明 |
|----------|-------------|------|
| `POST /api/v1/committee/meetings/{id}/submit-vote` | ⚠️ **已调用但待修复**（仅代填） | `meeting_id` 硬编码为 0（见 B5），且 payload 为 `{ votes: {...} }` 不符合 §3.6 结构，缺少 `committee_type`、`vote_dimension`、`section_a` 等字段（见 B5 补充） |
| `GET /api/v1/committee/meetings?type=ficc` | ❌ 待对接 | 替换本地 Mock `ficcMeetingList` |
| `POST /api/v1/committee/meetings` | ❌ 待对接 | 替换本地 `quickCreateFiccMeeting()` |
| `DELETE /api/v1/committee/meetings/{id}` | ❌ 待对接 | 替换本地 `deleteFiccMeeting()` |
| `GET /api/v1/committee/page-context?committee_type=ficc` | ❌ 待对接 | |
| `GET /api/v1/committee/mixed/sessions?committee_type=ficc` | ❌ 待对接 | 替换本地 Mock `ficcMemberScores` |
| `GET /api/v1/committee/mixed/sessions/history?committee_type=ficc` | ❌ 待对接 | 替换本地 Mock |
| `POST /api/v1/committee/mixed/remind` | ❌ 待对接 | 替换本地 `sendFiccReminder()` |
| `GET /api/v1/workspace/portal-snapshot` | ❌ 待对接 | FICC 视图需接入以获取决议表 |

### 4.4 FiccCommitteeView — 仍使用 Mock 数据的功能（待后端 API）

| # | Mock 变量名 | 待对接 API |
|---|------------|-----------|
| F1 | `FICC_COMMITTEE_MEMBERS` | `GET /api/v1/auth/me` + 用户目录 API |
| F2 | `ficcMeetingList` | `GET /api/v1/committee/meetings?type=ficc` |
| F3 | `ficcMaterials` | `GET /api/v1/committee/mixed/sessions?committee_type=ficc` |
| F4 | `FICC_MEMBER_ATTACHMENTS` | 待附件上传/列表 API（新增） |
| F5 | `ficcMemberScores` | `GET /api/v1/committee/mixed/sessions?committee_type=ficc` |
| F6 | `ficcQMemberScores` | `GET /api/v1/committee/mixed/sessions/history?committee_type=ficc&vote_dimension=quarterly` |
| F7 | `ficcBallots`（position/duration/equity） | `POST /api/v1/committee/meetings/{id}/submit-vote`（`ficc_position_pct` 等字段，见 §3.6） |
| F8 | `CROSS_MIXED_MOCK` | `GET /api/v1/committee/page-context`（混合投委会上下文） |
| F9 | `FICC_MOCK_FILES` | 待文件管理 API（新增） |
| F10 | `FICC_HISTORY_OPINIONS` | `GET /api/v1/committee/mixed/sessions/history?committee_type=ficc` |
| F11 | `FICC_PREV_PERIOD_REVIEW` | `GET /api/v1/committee/mixed/sessions/history?committee_type=ficc&limit=1` |
| F12 | `FICC_CONSENSUS_TABLE` | 由 `GET /api/v1/committee/mixed/sessions` 响应数据前端计算得出 |
| F13 | `handleIssue()` | 待发行执行 API（新增） |
| F15 | `sendFiccReminder()` | `POST /api/v1/committee/mixed/remind` |

### 4.5 文档已定义但前端均未调用的接口

> **注意**: 以下接口在本仓库中无后端实现代码可核验，状态基于文档定义和前端代码交叉审计。

| 后端接口 | 说明 | 前端状态 |
|----------|------|----------|
| `GET /api/v1/auth/me` | 获取当前用户信息 | **未对接**（前端使用 hardcoded JWT + role 切换） |
| `POST /api/v1/committee/mixed/submit` | 提交混合问卷（独立会期） | **未对接**（前端有 UI 但当前用 `submit-vote` 替代） |
| `POST /api/v1/committee/meetings/{id}/publish` | 发布决议 | **未对接**（前端 `handleSubmitDecision()` 仅修改本地状态，不调用任何发布 API；Tab `minutes` 中也无归档按钮调用此端点） |
| `POST /api/v1/committee/meetings/{id}/resolution` | 主任委员资配决议 | **未对接**（`handleSubmitDecision()` 仅写本地 `deptAllocationDecision`，未发 HTTP 请求；见 §3.8 及 B8） |
| `GET /api/v1/asset-allocation/*` | 全部 SAA 相关接口 | **未对接** |
| `POST /api/v1/orchestrator/commands` | 命令派发 | **未对接** |
| `GET /api/v1/messages/events/stream` | SSE 实时推送 | **未对接** |

### 4.6 前端认证现状

前端当前使用 **hardcoded JWT** (`HARDCODED_DEV_BEARER`):
- 文件: `frontend/src/api/request.ts`
- Token 对应 `sub=1`，使用当前 `.env` 的 `SECRET_KEY` 生成
- 支持通过 `localStorage.map_access_token` 覆盖
- **仅适用于开发联调**，上线前须切换为 SSO 流程

---

## 五、数据字典

### 5.1 投委会资产配置字典（`UNIFIED_VOTE_CONFIG`）

后端需了解此字典，以正确解析 `section_a` 键名和 `scores` 统计。

**混合投委会月度资产（6 项）**:

| id | 细分策略名（section_a key） | 大类 | 标的指数 | 当前点位 | 幅度类型 |
|----|-----------------------------|------|---------|---------|---------|
| `dividend_csi_total` | 红利 | 含权 | 中证红利全收益 | 11945.58 | pct |
| `equity_mixed_885001` | 偏股混 | 含权 | 885001 | 7228.45 | pct |
| `hktech_513310` | 恒生科技 | 含权 | 513310 | 4986.78 | pct |
| `gold_518880` | 黄金 | 另类 | 518880 | 7.283 | pct |
| `rate_10y` | 利率(10Y) | 固收 | 10Y国债活跃券 | 1.79 | bp |
| `rate_30y` | 利率(30Y) | 固收 | 30Y国债活跃券 | 2.281 | bp |

**FICC 投委会月度资产（6 项）**:

| id | 细分策略名（section_a key） | 大类 | 标的指数 | 当前点位 | 幅度类型 |
|----|-----------------------------|------|---------|---------|---------|
| `cd_1y_aaa` | 存单 | 固收 | 1Y AAA存单 | 1.4825 | bp |
| `credit_3y_aa_plus` | 信用 | 固收 | 3Y AA+中票 | 1.7814 | bp |
| `rate_10y` | 利率(10Y) | 固收 | 10Y国债活跃券 | 1.79 | bp |
| `rate_30y` | 利率(30Y) | 固收 | 30Y国债活跃券 | 2.281 | bp |
| `cb_csi_convert` | 转债 | 含权 | 中证转债 | 502.65 | pct |
| `bond_fund_885007` | 二级债基 | 含权 | 885007 | 5224.57 | pct |

**FICC 投委会季度资产（11 项）**:

| id | 细分策略名（key） | 大类 |
|----|-----------------|------|
| `q_cd_1y_aaa` | 存单(季) | 固收 |
| `q_credit_3y_aa_plus` | 信用(季) | 固收 |
| `q_rate_10y` | 利率10Y(季) | 固收 |
| `q_rate_30y` | 利率30Y(季) | 固收 |
| `q_cb_csi_convert` | 转债(季) | 含权 |
| `q_bond_fund_885007` | 二级债基(季) | 含权 |
| `q_dividend_csi_total` | 红利(季) | 含权 |
| `q_hktech_513310` | 恒生科技(季) | 含权 |
| `q_reits_csi_total` | REITs(季) | 含权 |
| `q_gold_518880` | 黄金(季) | 另类 |
| `q_crude_oil` | 原油(季) | 另类 |

### 5.2 档位分数映射（五档枚举）

> 后端 `section_a` 存储的是 1~5 的整数，不是中文字符串。

| 整数值 | 中文名 | bp 类含义（收益率） | pct 类含义（价格） |
|--------|--------|-------------------|-----------------|
| 1 | 谨慎 | 上行 15bp+ | -10%以下 |
| 2 | 中性偏谨慎 | 上行 5-15bp | -10% 到 -3% |
| 3 | 中性 | ±5bp 内 | -3% 到 3% |
| 4 | 中性偏乐观 | 下行 5-15bp | 3% 到 10% |
| 5 | 乐观 | 下行 15bp+ | 10%以上 |

**前端 `scoreToVoteChoice` 映射**（用于向 portal-snapshot 的 `winner` 对齐）:

| score | `winner` 值 |
|-------|------------|
| 1~2 | `underweight`（谨慎） |
| 3 | `neutral`（中性） |
| 4~5 | `overweight`（乐观） |

### 5.3 会议状态枚举

| 后端值（snake_case） | 前端中文映射 | 说明 |
|--------------------|------------|------|
| `draft` | 筹备中 | 会议创建后初始状态 |
| `voting` | 进行中 | 投票进行中 |
| `published` | 已结束 | 决议已发布，不可逆 |

**已废弃**：`DRAFT`、`VOTING`、`PUBLISHED`（大写）— 后端 API 不再接受大写枚举值。

### 5.4 会议类型枚举

| 后端值 | 前端中文映射 |
|--------|------------|
| `mixed` | 混合投委会（季度） |
| `ficc` | FICC 投委会（固定收益） |

**已废弃**：`MIXED`、`FICC`（大写）。

---

## 六、数据库模型（9 张表）

| 表名 | 用途 | 关键字段 |
|------|------|----------|
| `map_users` | 用户账户 | `portal_user_id`, `username` |
| `ic_meetings` | 投委会会议 | `meeting_code`, `title`, `type` (mixed/ficc), `status` (draft/voting/published) |
| `ic_vote_records` | 投票记录 | `meeting_id`, `user_id`, `committee_type`, `vote_dimension`, `choice_items` (JSON), `numeric_items` (JSON) |
| `ic_resolutions` | 已发布决议 | `meeting_id`, `aggregated_taa` (JSON), `ai_minutes` (TEXT) |
| `ic_chair_resolutions` | 主任委员资配决议 | `meeting_id`, `resolution_id`, `bond_grade`, `equity_grade`, `equity_mix` (JSON), `products` (JSON) |
| `ic_mixed_questionnaire_submissions` | 混合问卷提交 | `session_code`, `submitter_id`, `questionnaire_json` (JSON，三段式结构） |
| `saa_drafts` | SAA 草稿版本 | `user_id`, `status`, `version`, `calculation_result` (JSON) |
| `asset_class_configs` | 资产类别配置 | `asset_class`, `expected_return`, `volatility`, `weight_min`, `weight_max` |
| `pending_commands` | 跨域命令注册 | `command_type`, `unique_key`, `status`, `task_id` |

**`ic_vote_records` 表新增字段说明**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `committee_type` | VARCHAR(10) | `mixed` 或 `ficc`，用于区分两套投委会 |
| `vote_dimension` | VARCHAR(10) | `monthly` 或 `quarterly`，区分月度/季度填报 |
| `choice_items` | JSON | 嵌套结构：`{ "section_a": {资产名: 分数}, "section_b": {资产名: boolean}, "section_c": [...], "core_view": "...", "risk_flag": false }`（见 §3.6 落库示例）|
| `numeric_items` | JSON | 存储 `ficc_position_pct`、`ficc_duration_pct`、`ficc_equity_pct`（FICC 专有数值）|

---

## 七、中间件与基础设施

| 组件 | 状态 | 说明 |
|------|------|------|
| TDSQL (MySQL 8 兼容) | 已接入 | 端口 5400，async aiomysql 驱动 |
| SQLite | 可用 | `MAP_USE_SQLITE=true` 开发 fallback |
| Redis | 已接入 | 异步客户端，用于 portal-snapshot 缓存 |
| RocketMQ | 骨架模式 | producer + consumer 已注册，stub 状态 |
| Alembic | 已配置 | 数据库迁移工具 |
| Docker Compose | 可用 | 含 TDSQL + Redis + RocketMQ 初始化脚本 |

---

## 八、前端待修复的关键 Bug（配合本文档同步修复）

以下问题存在于前端代码中，需要前端在对接后端时一并修复，否则已对接接口仍会静默出错：

| # | 文件 | 位置 | 问题描述 | 修复方案 |
|---|------|------|---------|---------|
| B1 | `CommitteeView.vue` | `submitMemberForm()` / `submitMemberFormSelf()` | payload 顶层键为 `vote`，内嵌 `{ choice_items: {...}, numeric_items: {...} }`；与 §3.6 定义格式不符（§3.6 要求 `section_a`/`section_b`/`section_c` 在顶层） | 按 §3.6 格式重构 payload：`committee_type`、`vote_dimension`、`section_a`、`section_b`、`section_c` 均为顶层字段 |
| B2 | `CommitteeView.vue` | `submitMemberForm()` / `submitMemberFormSelf()` | `risk_flag` 被写入 `choice_items.risk_flag = 'true'`（字符串），§3.6 要求顶层 `risk_flag: boolean` | 提取到请求体顶层，类型改为 boolean |
| B3 | `CommitteeView.vue` | `submitMemberForm()` / `submitMemberFormSelf()` | `core_view` 被写入 `choice_items.core_view`（嵌套），§3.6 要求顶层 `core_view: string` | 提取到请求体顶层 |
| B4 | `CommitteeView.vue` | `quickCreateMeeting()` | `type: 'MIXED'` 大写，后端期望 `type: 'mixed'` 小写 | 改为 `type: 'mixed'` |
| B5 | `FiccCommitteeView.vue` | `submitFiccProxyScores()` | ① `submitVote(0, ...)` 硬编码 `meetingId=0`，会触发后端 404；② payload 为 `{ votes: {...} }`，不符合 §3.6 结构，缺少 `committee_type: "ficc"`、`vote_dimension`、`section_a` 等字段 | ① 改用 `resolveVotingMeetingId()` 获取正确会议 ID；② 按 §3.6 格式重构 payload |
| B6 | `demoStore.ts` | `ROLE_QUERY` | `班子→ADMIN`、`部门长→COMMITTEE_MEMBER`、`投管→PM` 存在语义重复 | 按 §3.1 角色映射表更新 |
| B7 | `CommitteeView.vue` | `loadMeetings()` | `http.get('/v1/committee/meetings')` 未传 `?type=mixed`，后端返回全部类型时混合页会混入 FICC 会议 | 改为 `http.get('/v1/committee/meetings', { params: { type: 'mixed' } })` |
| B8 | `CommitteeView.vue` | `handleSubmitDecision()` | 函数仅写入本地 `deptAllocationDecision.value`，未发送 HTTP 请求到 `POST /api/v1/committee/meetings/{id}/resolution`。刷新页面数据丢失 | 在 `handleSubmitDecision()` 中增加 `http.post('/v1/committee/meetings/${meetingId}/resolution', payload)` 调用 |

---

*文档版本: 2026-05-08 r3 v1.9.5 审计同步版 | 来源: 前端代码库交叉审计（`demoStore.ts`、`CommitteeView.vue`、`FiccCommitteeView.vue`）| 审计工具: Claude Code | 变更摘要: 同步 Tab 结构重构、新增 MACRO_INDICATORS/PRODUCT_PERF_ROWS Mock、修正 handleSubmitDecision 函数名、新增 B8 Bug 条目*
