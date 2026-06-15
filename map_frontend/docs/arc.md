# MAP (大类资产配置平台) 前后端架构设计规范

> **更新日期**：2026-05-09 · **对齐版本**：v1.9.5

---

## 1. 架构定位与核心思想

MAP 平台采用 **Hub & Spoke (枢纽-辐射)** 模式，定位为"轻量级编排中台与 AI 智脑"。
本系统不重复造轮子，不存储海量异构行情明细，而是作为资管体系的**资配指挥中心**。

**核心架构原则 (The Golden Rules):**

1. **消费者驱动契约 (Consumer-Driven Contract)**：MAP 作为需求方，定义并提供标准的 API 接口规范 (OpenAPI/Swagger)。所有被集成的外部系统必须开发 Adapter，主动将数据转换为 MAP 要求的格式进行推/拉。
2. **读写分离与双 Hub 隔离**：
   - **Data Hub (数据枢纽)**：负责"读"。对接外部数据源，清洗、统一数据字典，为模型和 UI 提供标准数据。
   - **Service Hub (服务枢纽)**：负责"写"与"算"。对接外部计算与执行引擎，通过工作流引擎串联模型试算、风控检查和指令下发。
3. **AI Native 准备度**：所有 API 设计必须是"大模型友好"的（JSON 结构扁平、语义清晰），为 AI Agent 自主调用（Function Calling）预留通道。

---

## 2. 系统架构图

```text
+-----------------------------------------------------------------------------------+
|                         MAP 前端交互层 (Vue 3.5 + TypeScript)                      |
|  [MAP门户] [投委会] [FICC投委会] [资配工作台] [调仓沙盘] [模型中心] [AI助手]        |
+-----------------------------------------------------------------------------------+
                                        | (REST / SSE / Axios)
                                        | baseURL = /api → proxy → :8000
+===================================================================================+
|                          MAP Backend (FastAPI / Python 3.10+)                      |
|                                                                                   |
|  +-------------------------+                     +-----------------------------+  |
|  |       Service Hub       |                     |          Data Hub           |  |
|  | (微服务编排 & 任务调度) | <======(融合)======>|  (数据字典 & 缓存 & 向量库) |  |
|  |                         |                     |                             |  |
|  | - 投委会状态机          |                     | - 基础资产标准化 (Master)   |  |
|  | - 编排器 (Orchestrator) |                     | - 市场行情缓存 (Redis)      |  |
|  | - SAA 计算引擎          |                     | - 投研知识向量库 (Milvus)   |  |
|  +-------------------------+                     +-----------------------------+  |
+===================================================================================+
       | (MAP 定义接口标准)                               | (MAP 定义数据 Schema)
       v                                                  v
+-----------------------+                      +------------------------------------+
|   内部计算/执行系统   |                      |           内部/外部数据源          |
|  (提供标准 API 实现)  |                      |        (提供标准 Data Feed)        |
+-----------------------+                      +------------------------------------+
| [组合分析] - 绩效/归因|                      | [数据魔方] - 内部持仓/流水         |
| [风控系统] - 事前试算 |                      | [Wind/DM]  - 宏观数据/债券行情     |
| [指令系统] - 交易下发 |                      | [信评系统] - 内部主体/债项评级     |
+-----------------------+                      +------------------------------------+
```

---

## 3. 前端架构

### 3.1 技术栈

| 层次 | 技术 | 版本 | 说明 |
|------|------|------|------|
| 框架 | Vue | 3.5.x | Composition API + SFC |
| 语言 | TypeScript | 5.8.x | 严格类型检查 |
| 构建 | Vite | 6.2.x | ESM 模块，端口 3000 |
| 样式 | Tailwind CSS | 4.1.x | v4 新语法 (`@import "tailwindcss"`) |
| 组件库 | Element Plus | 2.9.x | 按需引入 |
| 图表 | ECharts + vue-echarts | 5.6.x / 7.x | |
| HTTP | Axios | 1.15.x | `baseURL = /api`，30s 超时 |
| 状态管理 | 无 Pinia/Vuex | — | 纯 Vue 3 `ref()`/`reactive()`/`computed()` |

### 3.2 目录结构

```text
frontend/src/
  main.ts                    # 入口，createApp().mount('#root')
  App.vue                    # 根组件，Tab 导航 + 侧边栏
  index.css                  # AlphaMind 主题 CSS 变量 + Tailwind
  api/
    request.ts               # Axios 实例、JWT 认证、请求/响应拦截
  store/
    demoStore.ts             # 核心状态（角色、Mock 模式、投票、持仓）
    modelStore.ts            # 规则模型（3 个模型定义与执行引擎）
    intentStore.ts           # 跨组件通信（模型权重传递、导航）
  useFiccAllocationEngine.ts # FICC 配置引擎 composable
  components/
    MapPortal.vue            # MAP 门户（导航宫格 + 雷达 + AI 助手）
    ExecutiveDashboard.vue   # 总裁驾驶舱
    TerminalDashboard.vue    # 资配工作台（四层管线）
    CommitteeView.vue        # 混合投委会（5 Tab）
    FiccCommitteeView.vue    # FICC 投委会（4 Tab）
    DeptHeadView.vue         # 部门决策台
    BatchSimulator.vue       # 调仓沙盘
    SAASimulator.vue         # SAA 模拟器
    ModelCenterView.vue      # 模型中心
    MarketView.vue           # 市场洞察
    ViewpointWorkshop.vue    # 观点车间
    FactorWorkshop.vue       # 因子车间
    SettingsView.vue         # 系统设置
    StrategySlider.vue       # 策略滑块组件
```

### 3.3 导航与路由

应用**无 vue-router**，采用 `App.vue` 中的 `activeTab` ref 驱动 Tab 切换：

- `activeTab` 持久化到 `sessionStorage`
- 跨组件导航通过 `intentStore.navigationTarget` 事件桥接
- 组件间通过 `@navigate` emit 传递目标 Tab ID

### 3.4 状态管理模式

```text
demoStore.ts (核心)
  ├── activeRole         → 11 种角色，localStorage 持久化
  ├── isGlobalMock       → Mock 开关，localStorage 持久化
  ├── timelineState      → T+0 ~ T+3 时间引擎
  ├── isPenetrationMode  → SPV 穿透开关
  ├── taskBasket         → 买卖任务篮子（computed summary）
  ├── proFormaData       → ProForma 推演叠加引擎（computed）
  ├── portalSnapshot     → API 响应状态
  ├── committeePageContext → API 响应状态
  └── useApi<T>()        → Mock/API 双模式封装

modelStore.ts (模型)
  ├── RULE_MODELS        → 3 个规则模型定义
  └── executeRuleModel() → 模型执行引擎

intentStore.ts (桥接)
  ├── pendingModelWeights → 模型中心 → 资配工作台
  ├── navigationTarget    → 编程式导航
  └── batchContext        → 批量任务上下文
```

### 3.5 API 层设计

```text
request.ts
  ├── baseURL: VITE_API_BASE_URL (默认 /api)
  ├── Auth: hardcoded JWT (sub=1) 或 localStorage.map_access_token
  ├── 拦截器: Authorization header 自动注入
  └── 日志: committee/portal 路径请求/响应记录

useApi<T>(apiCall, mockFallback?)
  ├── isGlobalMock=true → 返回 mockFallback（500ms 延迟）
  ├── API 调用成功 → 返回响应数据
  └── API 调用失败 → 降级到 mockFallback
```

### 3.6 设计系统 (AlphaMind SPEC)

| Token | 值 | 用途 |
|-------|-----|------|
| `--am-bg-base` | `#161922` | 页面底色 |
| `--am-bg-panel` | `#1A1E2B` | 面板底色 |
| `--am-bg-card` | `#202431` | 卡片底色 |
| `--am-gain` | `#F04864` | 上涨/看多（红） |
| `--am-loss` | `#00C9A7` | 下跌/看空（绿） |
| `--am-warn` | `#FFAB00` | 预警（橙） |
| `--am-brand` | `#3B9EFF` | 品牌色/交互色 |
| `.am-title-bar` | 4px 竖线 | 标题装饰 |
| `.fin-table` | table-fixed, tabular-nums | 金融数据表格 |
| `.tab-trap` | 梯形 Tab | 导航 Tab 样式 |

---

## 4. 后端架构

### 4.1 技术栈

| 层次 | 技术 | 说明 |
|------|------|------|
| 框架 | FastAPI (Python 3.10+) | 异步，自动 OpenAPI 文档 |
| 数据库 | TDSQL (MySQL 8 兼容) | 端口 5400，aiomysql 异步驱动 |
| 缓存 | Redis | 异步客户端，portal-snapshot 缓存 |
| 消息队列 | RocketMQ | 骨架模式，stub 状态 |
| 迁移 | Alembic | 数据库版本管理 |
| 认证 | SSO + JWT | HttpOnly Cookie `mapToken` + Bearer Header |

### 4.2 API 规范

| 项目 | 值 |
|------|-----|
| 服务基础路径 | `/api` |
| API 前缀 | `/api/v1` |
| 自动文档 | `/docs` (Swagger UI), `/redoc` (ReDoc) |
| 健康检查 | `GET /health` |
| 命名规范 | 全量 `snake_case`（JSON 字段、Query/Path 参数） |
| 枚举值 | 全小写（`mixed`、`ficc`、`draft`、`voting`、`published`） |

### 4.3 数据模型（9 张表）

| 表名 | 用途 | 关键字段 |
|------|------|---------|
| `map_users` | 用户账户 | `portal_user_id`, `username` |
| `ic_meetings` | 投委会会议 | `meeting_code`, `type`, `status` |
| `ic_vote_records` | 投票记录 | `meeting_id`, `user_id`, `choice_items` (JSON), `numeric_items` (JSON) |
| `ic_resolutions` | 已发布决议 | `meeting_id`, `aggregated_taa` (JSON), `ai_minutes` (TEXT) |
| `ic_chair_resolutions` | 主任委员决议 | `meeting_id`, `equity_grade`, `products` (JSON) |
| `ic_mixed_questionnaire_submissions` | 混合问卷提交 | `session_code`, `questionnaire_json` (JSON) |
| `saa_drafts` | SAA 草稿 | `user_id`, `status`, `calculation_result` (JSON) |
| `asset_class_configs` | 资产类别配置 | `asset_class`, `expected_return` |
| `pending_commands` | 跨域命令 | `command_type`, `unique_key`, `status` |

> **架构约束**：无物理外键，跨表关系使用逻辑 ID + 索引。

---

## 5. Data Hub 契约设计

Data Hub 采用 **拉取缓存 (Pull-and-Cache)** 模式。MAP 按标准化 Schema 拉取数据。

### 5.1 资产主数据接口 (Asset Master)

**MAP 要求外部提供的接口格式：**

```
GET /api/v1/map-hub/data/assets/{asset_code}
```

```json
{
  "asset_code": "019686.SH",
  "asset_name": "22附息国债24",
  "asset_class": "FI",
  "metrics": {
    "price": 102.45,
    "yield_to_maturity": 2.15,
    "modified_duration": 4.82,
    "credit_rating_internal": "AAA",
    "dv01": 0.045
  },
  "update_time": "2026-03-31T09:00:00Z"
}
```

---

## 6. Service Hub 契约设计

Service Hub 采用**事件驱动**与**异步调用**模式。

### 6.1 组合试算服务

```
POST /api/v1/map-hub/service/portfolio/simulate
```

```json
{
  "portfolio_id": "PORT_A001",
  "intent_actions": [
    {"action": "SELL", "asset": "019686.SH", "weight_change": -0.05},
    {"action": "BUY", "asset": "512890.SH", "weight_change": 0.05}
  ],
  "benchmark_id": "BMK_001"
}
```

### 6.2 调仓指令下发服务

```
POST /api/v1/map-hub/service/trade/execute
```

```json
{
  "intent_snapshot_id": "SNAP_20260331_001",
  "authorizer_id": "PM_007",
  "execution_strategy": "TWAP",
  "orders": [
    {"ticker": "512890.SH", "side": "BUY", "amount_cny": 5000000}
  ]
}
```

---

## 7. 系统对接协同原则 (SOP)

1. **接口先行 (API-First)**：后端 API 文档即为强契约。前端基于契约开发，后端提供 Mock Server。
2. **防腐层要求 (Anti-corruption Layer)**：外部系统数据与 MAP 格式不符时，由外部系统开发适配器，MAP 后端不处理异构脏数据。
3. **幂等性与重试机制**：所有 POST/PUT 请求须支持幂等性（基于 `meeting_code`、`session_code + submitter_id` 等唯一键），防止重复提交。
4. **前端双轨 Mock**：前端通过 `useApi()` 封装实现 Mock/API 双模式，联调时可逐步切换，互不阻塞。
5. **命名规范强约束**：后端 `snake_case`，前端本地 `camelCase`，API 边界由前端自行映射。

---

*文档版本: 2026-05-09 · 基于 v1.9.5 前端代码审计 + 后端 API 接口文档*
