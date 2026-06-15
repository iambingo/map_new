# PROJECT · MAP 大类资产管理平台 · 进度文档

> **更新日期**：2026-05-09 · **当前版本**：v1.9.5 · **当前阶段**：前后端联调

---

## 1. 项目概览

| 项目 | 内容 |
|---|---|
| 项目名称 | MAP · 大类资产管理平台 |
| 启动日期 | 2026-03-20 |
| 前端技术栈 | Vue 3.5 + TypeScript 5.8 + Vite 6.2 + Tailwind CSS 4.1 + Element Plus 2.9 + ECharts 5.6 |
| 后端技术栈 | FastAPI (Python 3.10+) + TDSQL (MySQL 8) + Redis + RocketMQ |
| 文档仓库 | `docs/prd.md` · `docs/arc.md` · `docs/project.md` · `docs/后端API接口文档.md` |
| 代码统计 | 14 个 Vue 组件 + 4 个 TS 模块，共 ~20,205 行 |

---

## 2. 里程碑规划

| 阶段 | 名称 | 目标 | 计划完成 | 状态 |
|---|---|---|---|---|
| Phase 0 | 项目初始化 | 建立项目结构、文档框架、开发环境 | 2026-03-20 | ✅ 完成 |
| Phase 1 | 前端核心搭建 | Vue 3 工程可运行、Tab 导航、组件库接入、主题系统 | 2026-04-23 | ✅ 完成 (v1.1) |
| Phase 2 | 核心功能 · 一期 | 门户、投委会、FICC 投委会、资配工作台 UI 全部完成 | 2026-05-07 | ✅ 完成 (v1.8) |
| Phase 3 | 前后端联调 | API 契约对齐、Mock→API 切换、投票/决议接口调试 | — | 🟡 进行中 |
| Phase 4 | 核心功能 · 二期 | 实时行情接入、SPV 穿透引擎、T+N 交收推演 | — | ⬜ 待开始 |
| Phase 5 | 高级功能 | AI 助手、报告生成、数据导入导出 | — | ⬜ 待开始 |
| Phase 6 | 部署上线 | SSO 接入、Docker 化、CI/CD、生产环境 | — | ⬜ 待开始 |

---

## 3. 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|---------|
| v1.0 | 2026-04-23 | 前端工程脚手架、基础布局、Tab 导航 |
| v1.1 | 2026-04-23 | 投委会核心功能：委员投票、决议展示 |
| v1.2 | 2026-04-23 | 资配工作台：四层管线、产品选择 |
| v1.3 | 2026-04-24 | FICC 投委会视图、FICC 配置引擎 |
| v1.4 | 2026-04-29 | 调仓沙盘、SAA 模拟器、部门决策台 |
| v1.5 | 2026-05-06 | 模型中心、观点车间、因子车间 |
| v1.6 | 2026-05-06 | 市场洞察、总裁驾驶舱、系统设置 |
| v1.7 | 2026-05-07 | API 契约审计、后端接口文档编写、Bug 清单 |
| v1.8 | 2026-05-07 | 投委会 API 部分对接（portal-snapshot、page-context） |
| v1.9 | 2026-05-08 | Tab 结构重构（Step→Tab）、市场及产品表现回顾 Tab、知行果复盘 Tab |

---

## 4. 前端功能清单

### 4.1 已完成

| ID | 功能 | 组件 | 备注 |
|---|---|---|---|
| FE-001 | MAP 门户首页（三栏布局：导航 + 工作台 + AI助手） | `MapPortal.vue` | AI 助手需 Gemini Key |
| FE-002 | 11 角色切换系统 | `demoStore.ts` | localStorage 持久化 |
| FE-003 | 投委会决策全流程（创建→投票→讨论→决议→归档） | `CommitteeView.vue` | 5 Tab 结构 |
| FE-004 | FICC 投委会决策全流程 | `FiccCommitteeView.vue` | 4 Tab 结构 |
| FE-005 | 秘书代填模式（Proxy Voting） | `demoStore.ts` | 支持混合/FICC |
| FE-006 | 资配工作台（TAA→Intent→ProForma→Execution 四层管线） | `TerminalDashboard.vue` | ProForma 引擎可用 |
| FE-007 | 调仓沙盘（单产品/批量模式、任务篮子） | `BatchSimulator.vue` | |
| FE-008 | SAA 模拟器（Monte Carlo UI、约束滑块） | `SAASimulator.vue` | 计算 Mock |
| FE-009 | 模型中心（规则模型执行、模型目录） | `ModelCenterView.vue` | 3 个规则模型可用 |
| FE-010 | 部门决策台（资配拆解、产品指引） | `DeptHeadView.vue` | |
| FE-011 | 总裁驾驶舱（KPI 概览、AUM/收益/回撤） | `ExecutiveDashboard.vue` | |
| FE-012 | 市场洞察（策略基准收益表） | `MarketView.vue` | |
| FE-013 | 观点车间（Feed/Card 布局、富文本编辑器） | `ViewpointWorkshop.vue` | |
| FE-014 | 因子车间（因子库表格、IC/IR 排序） | `FactorWorkshop.vue` | |
| FE-015 | 全局深色主题 CSS 变量体系 (AlphaMind SPEC) | `index.css` | |
| FE-016 | 双轨 Mock 模式（构建时 + 运行时 + API 级降级） | `demoStore.ts` | |

### 4.2 进行中（Phase 3 — 联调）

| ID | 功能 | 状态 | 备注 |
|---|---|---|---|
| FE-017 | 投票 payload 重构（B1-B3） | 待修复 | 当前 payload 结构不符合 API 契约 |
| FE-018 | 主任委员决议 API 对接（B8） | 待实现 | `handleSubmitDecision()` 仅本地状态 |
| FE-019 | FICC 投票 API 修复（B5） | 待修复 | `meetingId=0` 硬编码 |
| FE-020 | 会议类型参数修复（B4） | 待修复 | `MIXED`→`mixed` |
| FE-021 | 会议列表过滤（B7） | 待修复 | 未传 `?type=mixed` |
| FE-022 | ROLE_QUERY 映射修正（B6） | 待修正 | 班子/部门长/投管 语义重复 |
| FE-023 | FICC 视图 9 个端点全面对接 | 待实现 | 当前全部 Mock |

### 4.3 待开始（Phase 4+）

| ID | 功能 | 优先级 | 模块 |
|---|---|---|---|
| FE-024 | SSO 认证流程接入 | P0 | Auth |
| FE-025 | SSE 实时事件流对接 | P1 | Infra |
| FE-026 | 实时行情数据源接入 | P1 | Market |
| FE-027 | SPV 穿透引擎（通道型/委外型双视角） | P1 | Terminal |
| FE-028 | T+N 交收推演引擎 | P1 | Batch |
| FE-029 | 宏观指标数据源接入 | P2 | Portal |
| FE-030 | 产品业绩排行数据源接入 | P2 | Portal |
| FE-031 | 数据中心模块 | P2 | DataCenter |
| FE-032 | AI 投研助手（Gemini 对接） | P2 | AI |

---

## 5. 后端接口对接状态

> 完整 Schema 与对接清单见 `docs/后端API接口文档.md`。

### 5.1 已定义的 API 端点（后端 9 张表）

| 模块 | 端点数 | 前端已调用 | 待对接 |
|------|--------|-----------|--------|
| 认证 (`/api/v1/auth`) | 2 | 0 | 2 |
| 投委会 (`/api/v1/committee`) | 6 | 6 (部分待修复) | 0 |
| 混合问卷 (`/api/v1/committee/mixed`) | 4 | 4 | 0 |
| 工作空间 (`/api/v1/workspace`) | 1 | 1 | 0 |
| 编排器 (`/api/v1/orchestrator`) | 2 | 0 | 2 |
| 资产配置 (`/api/v1/asset-allocation`) | 7 | 0 | 7 |
| 消息中心 (`/api/v1/messages`) | 2 | 0 | 2 |
| **合计** | **24** | **11** | **13** |

### 5.2 前端认证现状

- 文件：`frontend/src/api/request.ts`
- 当前使用 hardcoded JWT（`sub=1`），对应后端 DEBUG 模式
- 支持 `localStorage.map_access_token` 覆盖
- 仅适用于开发联调，上线前须切换为 SSO 流程

---

## 6. 已知风险与决策

| # | 风险/问题 | 影响 | 处理方案 |
|---|---|---|---|
| R-01 | 投票 payload 结构与 API 契约不一致 | 高 | 已列出 B1-B3 修复方案，联调阶段优先处理 |
| R-02 | FICC 视图几乎全量 Mock，联调工作量较大 | 中 | 按 F1-F15 逐步替换，优先投票和会议管理 |
| R-03 | 主任委员决议未持久化，刷新即丢失 | 中 | 需在 `handleSubmitDecision()` 中增加 HTTP 调用 |
| R-04 | ROLE_QUERY 存在语义冲突（班子/部门长/投管） | 中 | 需前后端同步修改 |
| R-05 | CommitteeView.vue 6229 行、FiccCommitteeView.vue 3587 行，维护困难 | 低 | 后续考虑拆分为子组件 |
| R-06 | AI 助手依赖 Gemini API Key，国内环境不稳定 | 低 | 后续考虑接入国内 LLM 或自部署 |
| R-07 | 外部数据源（Wind、估值表）尚未提供标准 API | 中 | 后端负责防腐层适配，前端统一走 Data Hub |
| R-08 | 无 vue-router，URL 不变导致无法深层链接 | 低 | 当前阶段可接受，后续按需引入 |

---

## 7. 变更日志

| 日期 | 版本 | 变更内容 |
|---|---|---|
| 2026-03-20 | v0.1.0 | 项目初始化，建立目录结构、三份文档、前后端脚手架 |
| 2026-03-20 | v0.2.0 | 基于 React TSX 原型重写 prd.md |
| 2026-04-18 | v0.4.0 | PRD 新增"通道型 SPV 穿透管理"与"T+N 动态交收时间轴" |
| 2026-04-23 | v1.0 | 前端 Vue 3 工程搭建完成，基础布局可运行 |
| 2026-04-29 | v1.4 | 核心业务组件全部完成（投委会、资配工作台、调仓沙盘） |
| 2026-05-06 | v1.6 | 辅助模块完成（模型中心、市场洞察、观点车间、因子车间） |
| 2026-05-07 | v1.7 | API 契约审计完成，后端接口文档编写 |
| 2026-05-08 | v1.9 | Tab 结构重构，市场及产品表现回顾、知行果复盘新增 |
| 2026-05-09 | — | 项目文档全面重写，对齐 v1.9.5 实际状态 |
