# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MAP (Multi-Asset Platform) — 机构级多资产配置与组合管理系统前端。Vue 3 单页应用，面向中国金融资管场景：投委会决策、组合配置、策略分析、市场洞察。

## Commands

```bash
cd frontend
npm run dev       # Vite dev server on port 3000, proxies /api → localhost:8000
npm run build     # vite build → dist/
npm run preview   # Preview production build
npm run lint      # tsc --noEmit (type check only, no eslint)
npm run clean     # rm -rf dist
```

无测试框架（无 vitest/jest），无 CI pipeline。

## Architecture

### 无 Router 的 Tab SPA

`App.vue` 是整个应用壳，通过 `activeTab` ref + `v-if/v-else-if` 链切换视图，**不使用 vue-router**。Tab 状态持久化到 `sessionStorage`。跨组件导航通过 `intentStore.ts` 的 `sharedIntentState.navigationTarget` 驱动。

### 无 Pinia 的响应式 Store

三个 store 模块（`src/store/`）使用纯 Vue 3 Composition API（`ref`/`reactive`/`computed`）：

- **`demoStore.ts`** — 主数据层（~1500行）：角色/权限、投委会投票、组合持仓、模拟数据开关、API 调用
- **`intentStore.ts`** — 跨组件通信：模型权重传递、导航意图、批量上下文
- **`modelStore.ts`** — 规则模型定义与执行引擎

### API 层

`src/api/request.ts` — Axios 实例，30s 超时，dev 环境硬编码 JWT。Vite 代理 `/api` → `http://127.0.0.1:8000`。

### Mock 机制

- `VITE_COMMITTEE_OFFLINE_MOCK=true`（`.env`）— 前端纯离线模式
- `isGlobalMock` — 运行时全局开关，组件内通过 `useApi<T>()` 自动 fallback 到 mock 数据

### 关键依赖

Vue 3.5 + Element Plus + ECharts/vue-echarts + Tailwind CSS v4（inline config，无独立 config 文件）+ clsx/tailwind-merge

### 视图组件（`src/components/`）

| 组件 | 业务域 |
|------|--------|
| `CommitteeView.vue` | 混合投委会（~6000行，最复杂） |
| `FiccCommitteeView.vue` | FICC 投委会 |
| `TerminalDashboard.vue` | 资产配置工作台 |
| `ExecutiveDashboard.vue` | 高管看板 |
| `DeptHeadView.vue` | 部门负责人决策 |
| `SAASimulator.vue` | 战略资产配置模拟器 |
| `BatchSimulator.vue` | 批量调仓沙盘 |

## Conventions

- **Commit 规范**：Conventional Commits（中文描述可接受），类型：`feat`/`fix`/`refactor`/`chore`/`docs` 等
- **样式**：Tailwind CSS v4 + 深色主题设计系统（定义在 `src/index.css`），类名合并用 `cn()`（clsx + twMerge）
- **组件风格**：`<script setup lang="ts">` + Composition API，单文件组件，组件内部直接消费 store 的 export
- **滚动容器**：实际滚动在 `App.vue` 的 `overflow-y-auto` div 上，子组件的 `overflow-y-auto` div 可能不是真正的滚动容器（`h-full` 在 `min-h-full` 父级下解析为 auto）。电梯导航等需要 scroll 事件的功能应向上查找真实滚动祖先。

## Agent Skills

This project uses [agent-skills](https://github.com/addyosmani/agent-skills) for structured engineering workflows.

**Skills directory:** `agent-skills/skills/` — read the relevant `SKILL.md` when the trigger matches.

| Command | Purpose |
|---------|---------|
| `/spec` | Define what to build (PRD before code) |
| `/plan` | Break work into small, verifiable tasks |
| `/build` | Implement one slice at a time |
| `/test` | Prove it works with tests |
| `/review` | Code review and quality gate |
| `/code-simplify` | Reduce complexity without changing behavior |
| `/ship` | Ship to production safely |
