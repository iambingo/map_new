# PRD · MAP 大类资产管理平台

> **版本**：v1.9 · **状态**：开发中（前后端联调阶段） · **更新日期**：2026-05-09
> **更新纪要**：全面重写，对齐 v1.9.5 前端实际实现状态。

---

## 1. 产品概述

### 1.1 背景与定位

MAP（Multi-Asset Platform）是面向**机构资产管理公司**（尤其是固收+基金经理团队、理财子公司）的**大类资产配置与投资决策协同系统**。

系统围绕一套清晰的**投资决策链路**运作：

```text
投资委员会 (Investment Committee)
    ↓ 宏观观点 + 公司级 SAA/TAA 目标
部门负责人 (Department Head)
    ↓ 部门级策略 TAA 微调与下发
基金经理 (Portfolio Manager)
    ↓ 意向组合构建 → T+N 组合推演 → 接力调仓指令生成
实际组合 (Actual Portfolio)
    ↓ 双视角持仓监控 (表层/穿透) + 偏离预警
```

### 1.2 核心概念

| 概念 | 英文 | 说明 |
|------|------|------|
| 基准组合 | SAA | 长期战略资产配置中枢，不频繁调整 |
| 目标组合 | TAA | 基于市场研判的战术性配置目标 |
| 意向组合 | Intent Portfolio | PM 在 TAA 框架内，构建至底层资产/SPV/个券的意向组合 |
| 实际组合 | Actual Portfolio | 当前真实持仓快照 |
| 纯委外 SPV | Active Outsourced | 外部主动管理的专户/基金，系统仅支持 T+1 估值表事后穿透 |
| 通道型 SPV | Passive Channel | 理财经理直接下达指令的影子账户，系统需支持 T+0 事前穿透与联合监控 |
| 交易日账本 | Trade Date Ledger | 侧重风险与敞口监控（指令下达即扣除敞口） |
| 交收日账本 | Settlement Date Ledger | 侧重流动性与头寸监控（资金真实到账才计入可用） |

---

## 2. 核心工作流

### 2.1 投委会定调 (Committee)

通过异步状态机，汇聚定量模型与定性观点，签发全局配置指引。

**两套投委会并行运行：**

| 投委会 | 类型标识 | 月度资产数 | 季度资产数 | Tab 结构 |
|--------|---------|-----------|-----------|---------|
| 混合投委会 | `mixed` | 6 项（红利、偏股混、恒生科技、黄金、利率10Y、利率30Y） | — | 市场及产品表现回顾 → 知行果复盘 → 委员观点 → 配置指引 → 会议纪要 |
| FICC 投委会 | `ficc` | 6 项（存单、信用、利率10Y、利率30Y、转债、二级债基） | 11 项（含红利、恒生科技、REITs、黄金、原油） | 委员观点 → 市场及产品表现回顾 → 配置指引 → 会议纪要 |

**委员评分体系（五档枚举）：**

| 整数 | 中文 | bp 类含义 | pct 类含义 |
|------|------|----------|-----------|
| 1 | 谨慎 | 上行 15bp+ | -10%以下 |
| 2 | 中性偏谨慎 | 上行 5-15bp | -10% 到 -3% |
| 3 | 中性 | ±5bp 内 | -3% 到 3% |
| 4 | 中性偏乐观 | 下行 5-15bp | 3% 到 10% |
| 5 | 乐观 | 下行 15bp+ | 10%以上 |

### 2.2 部门下达 (Dept Head)

部门长在此基础上，结合部门产品特性（如低波、中低波）拆解配置比例。

### 2.3 基金经理试算 (PM - Simulator)

- **T+N 时间轴**：模拟未来现金流与资金交收。
- **穿透合并**：结合通道型 SPV 与直投资产进行偏离度测算。
- **指令生成与路由**：根据资产属性，将指令准确下发至直投交易席位或通道方交易席位。

---

## 3. 功能模块与实现状态

### 3.1 模块总览

| 模块 | 组件 | 代码量 | 实现状态 |
|------|------|--------|---------|
| MAP 门户 | `MapPortal.vue` | 1308 行 | ✅ UI 完成，数据 Mock |
| 总裁驾驶舱 | `ExecutiveDashboard.vue` | 344 行 | ✅ UI 完成，数据 Mock |
| 资配工作台 | `TerminalDashboard.vue` | 2617 行 | ✅ UI 完成，ProForma 引擎可用，持仓 Mock |
| 混合投委会 | `CommitteeView.vue` | 6229 行 | ⚠️ UI 完成，部分 API 已对接，payload 待修复 |
| FICC 投委会 | `FiccCommitteeView.vue` | 3587 行 | ⚠️ UI 完成，大部分 Mock，代填 API 待修复 |
| 部门决策台 | `DeptHeadView.vue` | 317 行 | ✅ UI 完成，数据 Mock |
| 调仓沙盘 | `BatchSimulator.vue` | 1291 行 | ✅ UI 完成，数据 Mock |
| SAA 模拟器 | `SAASimulator.vue` | 785 行 | ✅ UI 完成，计算 Mock |
| 模型中心 | `ModelCenterView.vue` | 1683 行 | ⚠️ 规则模型可用，AI 模型 Mock |
| 市场洞察 | `MarketView.vue` | 421 行 | ✅ UI 完成，数据 Mock |
| 观点车间 | `ViewpointWorkshop.vue` | 549 行 | ✅ UI 完成，数据 Mock |
| 因子车间 | `FactorWorkshop.vue` | 650 行 | ✅ UI 完成，数据 Mock |
| 系统设置 | `SettingsView.vue` | 341 行 | ⚠️ UI 布局完成，功能禁用 |
| **合计** | **14 个组件** | **~20,205 行** | |

### 3.2 角色体系（11 种角色）

| 角色 | ROLE_QUERY | 所属模块 |
|------|-----------|---------|
| 班子 | `ADMIN` | 高管层 |
| 部门长 | `COMMITTEE_MEMBER` | 部门层 |
| 投资经理 | `PM` | 执行层 |
| 投资助理 | `ANALYST` | 执行层 |
| 投管 | `PM` | 执行层 |
| 混合投资委员会秘书 | `COMMITTEE_SECRETARY` | 混合投委会 |
| 混合投资委员会委员 | `COMMITTEE_MEMBER` | 混合投委会 |
| 混合投资委员会主任委员 | `COMMITTEE_CHAIR` | 混合投委会 |
| FICC投资委员会秘书 | `FICC_SECRETARY` | FICC 投委会 |
| FICC投资委员会委员 | `FICC_MEMBER` | FICC 投委会 |
| FICC投资委员会主任委员 | `FICC_CHAIR` | FICC 投委会 |

> **已知问题**：`班子→ADMIN`、`部门长→COMMITTEE_MEMBER`、`投管→PM` 存在语义重复，需按目标映射表修正。

### 3.3 导航结构

应用采用**单页 Tab 切换架构**（无 vue-router），Tab 定义如下：

| Tab ID | 中文标签 | 分组 |
|--------|---------|------|
| `portal` | MAP门户 | 工作室 |
| `viewpoint` | 观点车间 | 工作室 |
| `factor` | 因子车间 | 工作室 |
| `executive` | 总裁驾驶舱 | 业务流 |
| `terminal` | 资配工作台 | 业务流 |
| `committee` | 投委会决策 | 业务流 |
| `ficc-committee` | FICC 委员会 | 业务流 |
| `dept-head` | 部门决策 | 业务流 |
| `batch-simulator` | 调仓沙盘 | 业务流 |
| `market` | 市场洞察 | 业务流 |
| `model-center` | 模型中心 | 业务流 |
| `data-center` | 数据中心 | 系统（开发中） |
| `settings` | 系统设置 | 系统 |

---

## 4. 架构与数据模型

### 4.1 前端状态管理

无 Pinia/Vuex，使用 Vue 3 Composition API 的 `ref()`/`reactive()`/`computed()` 模式。

**核心 Store（`frontend/src/store/`）：**

| 文件 | 用途 |
|------|------|
| `demoStore.ts` (1447 行) | 核心状态：角色切换、Mock 模式、API 对接、投票引擎、T+N 时间轴、SPV 穿透、任务篮子、ProForma 叠加引擎 |
| `modelStore.ts` (144 行) | 规则模型定义与执行（3 个模型：总量平均分配、净资产等比分摊、资产浓度控制） |
| `intentStore.ts` (32 行) | 跨组件通信：模型权重传递、导航目标、批量上下文 |

**关键业务引擎（已实现功能性逻辑）：**

| 引擎 | 位置 | 说明 |
|------|------|------|
| ProForma 叠加引擎 | `demoStore.ts` | 在 Mock 持仓上叠加任务篮子指令，生成推演组合 |
| 投票分布计算器 | `demoStore.ts` | 按 `scoreToVoteChoice` 映射计算 `overweight/neutral/underweight` 分布 |
| FICC 配置引擎 | `useFiccAllocationEngine.ts` | 低配/平配/高配分层、久期/含权率层级计算、偏离度预警 |
| 规则模型执行器 | `modelStore.ts` | 3 个规则模型的实时计算与预览输出 |

### 4.2 数据流向

```text
外部系统（数据魔方、Wind、估值表）
        ↓ (Data Hub 拉取缓存)
MAP 后端 (FastAPI /api/v1)
        ↓ (REST + SSE)
MAP 前端 (Vue 3)
    ├── 直连 API（Axios + useApi Mock 双模式）
    └── 跨组件状态（intentStore 事件桥接）
```

### 4.3 双轨 Mock 模式

系统设计了双层 Mock 机制：

| 层级 | 控制 | 效果 |
|------|------|------|
| 构建时 | `VITE_COMMITTEE_OFFLINE_MOCK=true` | 编译时禁用后端调用 |
| 运行时 | `isGlobalMock` ref（localStorage 持久化） | UI 开关实时切换 |
| API 级 | `useApi<T>()` 封装 | API 失败时自动降级到 Mock 数据 |

---

## 5. UI/UX 视觉规范 (The AlphaMind SPEC)

| 规范项 | 值 |
|--------|-----|
| 核心主题 | 深蓝灰极客风格（#161922 底色, #1A1E2B 面板） |
| 数字表格 | `table-fixed`、等宽列、`font-mono tabular-nums text-right` |
| 上涨/看多 | `#F04864`（红） |
| 下跌/看空 | `#00C9A7`（绿） |
| 预警 | `#FFAB00`（橙） |
| 标题修饰 | `am-title-bar` 粗竖线 |
| 通道资产标识 | 蓝色 `[通道透视]` 徽章 |
| 委外资产标识 | 橙色 `[委外盲盒]` 徽章 |

---

## 6. 技术架构

| 技术 | 版本 | 说明 |
|------|------|------|
| Vue | 3.5.x | 前端框架 |
| TypeScript | 5.8.x | 类型安全 |
| Vite | 6.2.x | 构建工具 |
| Tailwind CSS | 4.1.x | 样式框架（v4 新语法） |
| Element Plus | 2.9.x | UI 组件库 |
| ECharts | 5.6.x + vue-echarts 7.x | 可视化图表 |
| Axios | 1.15.x | HTTP 客户端 |
| FastAPI | Python 3.10+ | 后端框架 |
| TDSQL | MySQL 8 兼容 (端口 5400) | 数据库 |
| Redis | — | 缓存（portal-snapshot） |

---

## 7. 专项功能规约

### 7.1 通道型 SPV 嵌套与穿透视图管理

| 口径 | 适用场景 |
|------|---------|
| 穿透后（经济敞口） | TAA 目标下达、偏离度监控、双十集中度测算、Campisi 归因 |
| 穿透前（结构视角） | 高管对手方风险监控、流动性测算、估值表对账 |

前端通过 `isPenetrationMode` ref 控制双口径切换。

### 7.2 T+N 动态时间轴与交收推演

| 账本 | 机制 | 用途 |
|------|------|------|
| 交易日账本 | 生成指令即时调整敞口 | 实时卡控市场风险 |
| 交收日账本 | 严格按 T+1/T+2 清算规则记账 | 把控流动性 |

前端通过 `timelineState` ref（T+0 至 T+3）控制时间轴漫游。

---

## 8. 待实现与待修复清单

> 详细接口对接状态见 `docs/后端API接口文档.md`。

### 8.1 高优先级（阻塞联调）

| # | 项目 | 说明 |
|---|------|------|
| 1 | 投票 payload 重构 | `submitMemberForm()` payload 结构不符合 API 契约（B1-B3） |
| 2 | 主任委员决议对接 | `handleSubmitDecision()` 仅写本地状态，未调用 `POST /resolution`（B8） |
| 3 | FICC 投票 API 修复 | `meetingId=0` 硬编码，payload 缺少 `committee_type`（B5） |
| 4 | 会议类型参数修复 | `type: 'MIXED'` 应改为 `'mixed'`（B4） |

### 8.2 中优先级（功能完整性）

| # | 项目 | 说明 |
|---|------|------|
| 5 | FICC 视图全面 API 对接 | 9 个端点仍为 Mock（F1-F11） |
| 6 | 发布决议 API 对接 | `POST /publish` 前端未调用 |
| 7 | ROLE_QUERY 映射修正 | 班子/部门长/投管 语义重复（B6） |
| 8 | `loadMeetings()` 过滤 | 未传 `?type=mixed`，会混入 FICC 会议（B7） |

### 8.3 低优先级（外部依赖）

| # | 项目 | 说明 |
|---|------|------|
| 9 | 宏观指标数据源 | `MACRO_INDICATORS` 等 Mock 数据需对接外部系统 |
| 10 | 产品业绩排行 | `PRODUCT_PERF_ROWS` 等需对接外部系统 |
| 11 | SSO 认证切换 | 当前 hardcoded JWT，上线前须切换 |
| 12 | SSE 实时推送 | `GET /messages/events/stream` 未对接 |

---

*文档版本: v1.9 · 2026-05-09 · 基于 v1.9.5 前端代码审计*
