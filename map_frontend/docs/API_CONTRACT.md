# 前后端 API 接口需求清单（API Contract）

> **生成日期**: 2026-04-27  
> **前端版本**: MAP Frontend v1.0  
> **Base URL**: `/api` (由 Vite proxy → `http://127.0.0.1:8000`)  
> **认证方式**: 待定（前端暂无 Auth Header）  
> **通用响应包装**: 所有接口返回 `axios response`，前端直接取 `res.data`

---

## 目录

- [一、混合投委会模块 (CommitteeView)](#一混合投委会模块)
- [二、FICC 投委会模块 (FiccCommitteeView)](#二ficc-投委会模块)
- [三、BFF 门户层 (demoStore)](#三bff-门户层)
- [四、待建模块（前端纯 Mock，后端需新建）](#四待建模块)
- [五、枚举值与业务映射](#五枚举值与业务映射)
- [六、WebSocket / SSE 依赖](#六websocket--sse-依赖)

---

## 一、混合投委会模块

### 1.1 获取会议列表

| 项目 | 说明 |
|------|------|
| **Endpoint** | `GET /v1/committee/meetings` |
| **用途** | 投委会会议中心门户页，加载所有会议（进行中/已结束/已归档） |
| **前端调用** | `loadMeetings()` → `useApi(() => http.get(...), MOCK_MEETINGS)` |

**Request**: 无参数

**Expected Response**:
```jsonc
[
  {
    "id": 1,                          // 必填, number
    "meeting_code": "IC-2025-Q4-...",  // 必填, string
    "title": "混合投委会 2025 Q4 配置决策会议",  // 必填, string
    "type": "MIXED",                   // 必填, string: "MIXED"
    "status": "已归档",                // 必填, enum: "待召开" | "进行中" | "已结束" | "已归档" | "已取消"
    "scheduled_at": "2025-10-15T14:00:00",  // 可选, string | null
    "created_by": 1,                   // 必填, number
    "created_at": "2025-10-01T10:00:00",  // 必填, string
    "updated_at": "2025-10-15T16:30:00"   // 必填, string
  }
  // ... 返回全部会议
]
```

**前端映射逻辑**: `title` → `name`, `scheduled_at` → `date` + `time`, `type` → `meetingType`

---

### 1.2 创建会议

| 项目 | 说明 |
|------|------|
| **Endpoint** | `POST /v1/committee/meetings` |
| **用途** | 秘书一键创建新会议（自动生成标题和编码） |
| **前端调用** | `quickCreateMeeting()` |

**Request Body**:
```json
{
  "meeting_code": "IC-2026-Q2-1509143023",
  "title": "2026 Q2 投资策略与TAA目标决议",
  "type": "MIXED"
}
```

**Expected Response**: 创建成功的会议对象（结构同 1.1 单条）。前端不解析响应体，仅调用 `loadMeetings()` 刷新列表。

**特殊逻辑**: 前端遇到 UNIQUE 冲突时自动重试最多 3 次（重新生成编码）。

---

### 1.3 删除会议

| 项目 | 说明 |
|------|------|
| **Endpoint** | `DELETE /v1/committee/meetings/{id}` |
| **用途** | 秘书删除"进行中"状态的会议 |
| **前置条件** | 仅 `isSecretary` + `status === '进行中'` + 用户二次确认 |

**Request**: URL path `{id}` = 会议 ID

**Expected Response**: 无需特定结构，HTTP 200 即可。

---

### 1.4 获取委员问卷提交记录

| 项目 | 说明 |
|------|------|
| **Endpoint** | `GET /v1/committee/mixed/sessions` |
| **用途** | 加载当前会期的委员问卷提交详情（评分、观点、风险标记） |
| **前端调用** | `loadMixedSubmissions()` → `useApi()` |

**Request**: 无参数（前端暂未传 session_code，建议后端返回当前活跃会期）

**Expected Response**:
```jsonc
{
  "session_code": "2026Q2",           // 可选
  "total": 6,                          // 可选, 提交总数
  "submissions": [
    {
      "id": 1,                         // 必填, number, 提交记录 ID
      "session_code": "2026Q2",        // 必填, string
      "submitter_id": 1,               // 必填, number, 委员 ID
      "submitted_at": "2026-04-15T14:12:00",  // 必填, string, ISO datetime
      "questionnaire_json": {          // 必填, object
        "section_a": {                 // 必填: 资产评分 1-5
          "债券": 4,                   // key=资产名, value=评分(1~5)
          "权益-红利": 3,
          "权益-成长": 3,
          "权益-价值": 3,
          "黄金": 4,
          "原油": 2
        },
        "section_b": {                 // 必填: 新高预判 true/false
          "债券": true,
          "权益-红利": false,
          "权益-成长": false,
          "权益-价值": false,
          "黄金": true,
          "原油": false
        },
        "section_c": [],               // 可选: 重点资产多选 string[]
        "core_view": "利率中枢大概率继续下移...",  // 必填, string
        "risk_flag": false             // 必填, boolean
      }
    }
    // ... 全部提交记录
  ]
}
```

**枚举值备注**: `section_a` 评分映射 → 1=极度看空, 2=偏空, 3=中性, 4=偏多, 5=极度看多

---

### 1.5 获取历史会期评分

| 项目 | 说明 |
|------|------|
| **Endpoint** | `GET /v1/committee/mixed/sessions/history` |
| **用途** | 跨会期资产评分对比折线图 |
| **前端调用** | `loadHistoryVotes()` |

**Request Params**: `?limit=10`

**Expected Response**:
```jsonc
{
  "sessions": [
    {
      "session_code": "2025Q4",       // 必填, string
      "submitted_count": 6,            // 必填, number
      "scores": {                      // 必填: 每个资产的统计
        "债券": {
          "avg": 3.8,                  // 必填, 均值
          "max": 5,                    // 必填, 最高分
          "min": 2,                    // 必填, 最低分
          "count": 6                   // 必填, 投票人数
        },
        "权益-红利": { "avg": 3.2, "max": 4, "min": 2, "count": 6 }
        // ... 每个资产类别
      }
    }
    // ... 最近 N 个会期
  ]
}
```

---

### 1.6 催办通知

| 项目 | 说明 |
|------|------|
| **Endpoint** | `POST /v1/committee/mixed/remind` |
| **用途** | 秘书向未提交问卷的委员发送催办通知 |

**Request Body**:
```json
{
  "member_name": "陈XX",
  "member_id": 1
}
```

**Expected Response**: HTTP 200 即可，无特定结构要求。

---

### 1.7 委员提交投票（模拟视角）

| 项目 | 说明 |
|------|------|
| **Endpoint** | `POST /v1/committee/meetings/{meetingId}/submit-vote` |
| **用途** | 委员提交问卷投票（选定委员视角或自身身份） |
| **前端调用** | `submitMemberForm()` / `submitMemberFormSelf()` |

**Request Body**:
```json
{
  "vote": {
    "choice_items": {
      "债券_view": "overweight",       // enum: "underweight" | "neutral" | "overweight"
      "权益-红利_view": "neutral",
      "权益-成长_view": "underweight",
      "权益-价值_view": "neutral",
      "黄金_view": "overweight",
      "原油_view": "underweight",
      "focus_asset": "黄金",           // 可选, 重点资产
      "risk_flag": "true",             // 可选, 风险标记
      "core_view": "利率中枢下移..."   // 可选, 核心观点
    },
    "numeric_items": {
      "债券_score": 4,                 // 1~5 整数
      "权益-红利_score": 3,
      "权益-成长_score": 2,
      "权益-价值_score": 3,
      "黄金_score": 5,
      "原油_score": 1
    }
  }
}
```

**Expected Response**: HTTP 200 即可。前端成功后调用 `fetchCommitteePageData()` 刷新。

---

## 二、FICC 投委会模块

> ⚠️ **当前状态**: FiccCommitteeView.vue 中 **所有数据均为前端硬编码 Mock**，无任何 API 调用。以下接口为 **前端期望后端新建** 的 API。

### 2.1 获取 FICC 会议列表

| 项目 | 说明 |
|------|------|
| **建议 Endpoint** | `GET /v1/ficc/meetings` |
| **用途** | FICC 投委会门户页会议列表 |

**Expected Response**:
```jsonc
[
  {
    "id": 1,                               // 必填
    "name": "FICC投委会 2025 Q4 配置决策会议",  // 必填
    "date": "2025.10.15",                   // 必填
    "time": "14:00-16:00",                  // 必填
    "location": "总部8楼FICC会议室",          // 必填
    "status": "已归档"                       // 必填: "待召开" | "进行中" | "已结束" | "已归档"
  }
]
```

---

### 2.2 获取 FICC 委员列表

| 项目 | 说明 |
|------|------|
| **建议 Endpoint** | `GET /v1/ficc/members` |
| **用途** | 委员材料提交进度、投票矩阵 |

**Expected Response**:
```jsonc
[
  { "id": "f1", "name": "张XX", "role": "固收投资主任" },
  { "id": "f2", "name": "李XX", "role": "利率策略" },
  // ... 7 名委员
]
```

---

### 2.3 获取/提交委员投研材料

| 项目 | 说明 |
|------|------|
| **建议 Endpoint** | `GET /v1/ficc/materials` / `POST /v1/ficc/materials` |
| **用途** | 查询委员投研材料提交状态 / 委员提交摘要+附件 |

**GET Response**:
```jsonc
{
  "f1": {
    "summary": "央行降准预期升温，利率债中长久期机会...",  // 必填
    "submittedAt": "14:12",                                 // 必填
    "attachments": [
      { "name": "Q2固收策略展望.pdf", "size": "2.4MB", "type": "pdf" }
    ]
  }
  // key=委员ID, 未提交的委员不出现
}
```

**POST Request Body**:
```json
{
  "member_id": "f3",
  "summary": "我的投研摘要...",
  "attachments": [{ "name": "报告.pdf", "size": "1.2MB", "type": "pdf" }]
}
```

---

### 2.4 获取量化模型锚点

| 项目 | 说明 |
|------|------|
| **建议 Endpoint** | `GET /v1/ficc/model-outputs` |
| **用途** | S2 步骤中的量化模型建议（蒙特卡洛/BL模型/风险平价） |

**Expected Response**:
```jsonc
[
  {
    "name": "SAA 蒙特卡洛模拟",       // 必填
    "badge": "MC-SAA",                // 必填
    "color": "#22D3EE",               // 必填, 主题色
    "desc": "基于10000次蒙特卡洛模拟...",  // 必填
    "anchorLabel": "建议久期使用率",    // 必填
    "anchorValue": "85%",             // 必填
    "anchorHint": "较上期 +5pct",      // 可选
    "showSandbox": true,              // 可选
    "highlight": true                 // 可选, 是否高亮
  }
  // ... 3 个模型
]
```

---

### 2.5 获取/提交 FICC 投票

| 项目 | 说明 |
|------|------|
| **建议 Endpoint** | `GET /v1/ficc/ballots` / `POST /v1/ficc/ballots` |
| **用途** | 获取全员投票矩阵 / 委员提交投票 |

**GET Response**:
```jsonc
{
  "f1": {
    "position": 80,         // 必填, 稳定资产仓位 0-100
    "duration": 65,         // 必填, 久期使用率 0-100
    "equity": 15,           // 必填, 含权使用率 0-100
    "submittedAt": "14:35"  // 必填
  }
  // ... 每个已投票委员
}
```

**POST Request Body**:
```json
{
  "member_id": "f3",
  "position": 75,
  "duration": 60,
  "equity": 20,
  "comment": "附加评论..."
}
```

---

### 2.6 获取 FICC 共识聚合表

| 项目 | 说明 |
|------|------|
| **建议 Endpoint** | `GET /v1/ficc/consensus` |
| **用途** | 投票聚合后的共识矩阵（按资产维度分组） |

**Expected Response**:
```jsonc
[
  {
    "asset": "现金类",                 // 必填, 资产大类
    "color": "#94A3B8",               // 必填
    "rows": [
      {
        "dim": "R007 走势",            // 必填, 维度名
        "consensus": "2.0~2.2%",       // 可选, 共识值
        "consensusType": "neutral",    // 可选: "bull" | "bear" | "neutral"
        "forecast": "维持平稳"          // 可选, 预测
      }
    ]
  }
  // ... 6 组资产
]
```

---

### 2.7 确认 FICC 最终决议

| 项目 | 说明 |
|------|------|
| **建议 Endpoint** | `POST /v1/ficc/decision` |
| **用途** | 主任委员确认本期 FICC 决议并下发 |

**Request Body**:
```json
{
  "meeting_id": 3,
  "product_decisions": {
    "lowVol": { "position": "中性", "duration": "中短久期", "equity": "低配" },
    "midLowVol": { "position": "中性偏积极", "duration": "中长久期", "equity": "标配" }
  },
  "special_advice": {
    "stableStructure": "建议维持...",
    "tenorStructure": "曲线策略偏陡峭化...",
    "creditBias": "信用利差收窄...",
    "equityBias": "转债市场...",
    "alternativeAdvice": "REITs..."
  }
}
```

**Expected Response**: HTTP 200 即可。

---

### 2.8 签发 FICC 会议纪要

| 项目 | 说明 |
|------|------|
| **建议 Endpoint** | `POST /v1/ficc/minutes/issue` |
| **用途** | 秘书签发终稿纪要并全系统同步 |

**Request Body**:
```json
{
  "meeting_id": 3
}
```

**Expected Response**: HTTP 200 即可。

---

### 2.9 催交通知

| 项目 | 说明 |
|------|------|
| **建议 Endpoint** | `POST /v1/ficc/reminders` |
| **用途** | 向未提交材料/投票的委员发送催交 |

**Request Body**:
```json
{
  "member_id": "f5",
  "type": "material"  // "material" | "ballot"
}
```

---

### 2.10 FICC 归因与策略数据

| 项目 | 说明 |
|------|------|
| **建议 Endpoint** | `GET /v1/ficc/attribution` / `GET /v1/ficc/strategies` |
| **用途** | 归因分析 + 策略红黑榜 |

**归因 Response**:
```jsonc
[
  { "name": "择时贡献", "timing": 45 },
  { "name": "择券贡献", "selection": 32 }
  // ... 5 条
]
```

**策略 Response**:
```jsonc
{
  "top": [
    { "name": "XX利率债A", "type": "纯债", "return": "+4.2%", "sharpe": "1.8" }
  ],
  "bottom": [
    { "name": "XX信用债C", "issue": "信用事件", "return": "-2.1%", "maxdd": "-5.3%" }
  ]
}
```

---

## 三、BFF 门户层

> 以下接口在 `demoStore.ts` 中被调用，供门户大盘和投委会共享使用。

### 3.1 获取门户快照

| 项目 | 说明 |
|------|------|
| **Endpoint** | `GET /v1/workspace/portal-snapshot` |
| **用途** | 门户大盘/投委会共享：拉取决议表、偏离分析、TAA 指引等 |
| **前端调用** | `fetchMeetingResolution()` / `fetchCommitteePageData()` |

**Request Params**: `?role=PM` (角色英文缩写，见枚举映射)

**Expected Response**:
```jsonc
{
  "snapshot_at": "2026-04-15T16:00:00",     // 必填
  "is_stale": false,                          // 必填
  "stale_reason": null,                       // 可选
  "taa_guidance": {
    "source_resolution": {                    // 可选
      "resolution_id": 1,
      "meeting_id": 3,
      "published_at": "2026-04-15T16:30:00"
    },
    "choice_results": {                       // 必填: 决议表
      "债券": {
        "winner": "overweight",               // "underweight" | "neutral" | "overweight"
        "vote_counts": { "overweight": 4, "neutral": 2, "underweight": 1 }
      },
      "权益": {
        "winner": "neutral",
        "vote_counts": { "overweight": 2, "neutral": 3, "underweight": 2 }
      }
      // ... 每个资产类别
    },
    "numeric_results": {},                    // 可选
    "published_at": "2026-04-15T16:30:00"    // 可选
  },
  "positions": null,                          // 可选
  "deviation_analysis": {},                   // 必填
  "rebalance_urgency": {
    "level": "medium",                        // "low" | "medium" | "high"
    "reason": "权益偏离度超阈值"
  },
  "navigation_tiles": []                      // 可选
}
```

---

### 3.2 获取投委会页面上下文

| 项目 | 说明 |
|------|------|
| **Endpoint** | `GET /v1/committee/page-context` |
| **用途** | 投委会页面加载时的只读上下文（会议信息、决议摘要、投票记录） |
| **前端调用** | `fetchCommitteePageData()` 并行调用 |

**Request**: 无参数

**Expected Response**:
```jsonc
{
  "meeting": {
    "id": 3,
    "meeting_code": "IC-2026-Q2-...",
    "title": "混合投委会 2026 Q2 投资策略与TAA目标决议",
    "type": "MIXED",
    "status": "进行中",
    "scheduled_at": "2026-04-15T14:00:00",
    "created_by": 1,
    "created_at": "2026-04-01T10:00:00",
    "updated_at": "2026-04-15T14:00:00"
  },
  "resolution": {
    "id": 1,
    "meeting_id": 3,
    "aggregated_taa": {                        // 聚合 TAA 决议
      "choice_results": { /* 同 3.1 */ }
    },
    "ai_minutes": "## 会议纪要\n...",           // AI 生成的纪要 Markdown
    "published_at": "2026-04-15T16:30:00",
    "published_by": 1,
    "created_at": "2026-04-15T16:00:00"
  },
  "votes": [
    { "user_id": 1, "submitted_at": "2026-04-15T14:12:00" },
    { "user_id": 2, "submitted_at": "2026-04-15T14:25:00" }
    // ... 投票记录
  ]
}
```

---

## 四、待建模块

> 以下模块在前端均为纯硬编码 Mock，无任何 API 调用。后端需按需新建对应接口。

### 4.1 终端仪表盘 (TerminalDashboard)

| 建议接口 | 用途 | 关键数据结构 |
|---------|------|-------------|
| `GET /v1/terminal/saa-benchmark` | SAA 基准配置 | `{ asset, target, range, deviation }` |
| `GET /v1/terminal/holdings` | 实际持仓（含 SPV 穿透） | `PositionItem { code, name, type, weight, mktValue, pnl, settlement_days, underlying[] }` |
| `GET /v1/terminal/cash` | 账面现金 + 在途资金 | `{ cash, cit[] }` |
| `GET /v1/terminal/timeseries` | 时序图表 | `{ actual[], intent[], taa[], saa[] }` |
| `GET /v1/terminal/pipeline` | 组合流水线 | `{ saa, taa, intent, actual }` |
| `GET /v1/terminal/inbox` | 收件箱任务 | `InboxTask { id, title, subtitle, urgent, affected, time, gridData }` |
| `GET /v1/terminal/securities` | 安全数据库搜索 | `SecurityItem { code, name, category, price, meta, type }` |

### 4.2 模型中心 (ModelCenterView)

| 建议接口 | 用途 | 关键数据结构 |
|---------|------|-------------|
| `GET /v1/models` | 模型列表（按分类） | `ModelItem { id, name, type, source, author, department, updateTime, desc, visibility, usageCount }` |
| `GET /v1/models/factors` | 可注入因子列表 | `InjectableFactor { id, name, refVar, shortVar, category, updateDate }` |
| `GET /v1/models/data-sources` | 数据源 Mock 表结构 | `{ name, tables[] }` |

### 4.3 因子工坊 (FactorWorkshop)

| 建议接口 | 用途 | 关键数据结构 |
|---------|------|-------------|
| `GET /v1/factors` | 因子列表 | `Factor { id, name, factorId, refVar, category, ic, icir, sharpe, turnover, coverage, description, models[], icHistory[] }` |

### 4.4 投研观点工坊 (ViewpointWorkshop)

| 建议接口 | 用途 | 关键数据结构 |
|---------|------|-------------|
| `GET /v1/viewpoints` | 观点列表 | `Viewpoint { id, author, role, title, tags, summary, highlight, likes, comments, views, sentiment, confidence }` |

### 4.5 批量模拟器 (BatchSimulator)

| 建议接口 | 用途 | 关键数据结构 |
|---------|------|-------------|
| `GET /v1/batch/inbox` | 收件箱调仓任务 | `Task { id, icon, title, subtitle, urgent, affected, time }` |
| `GET /v1/batch/drafts` | 方案草稿 | `Draft { id, label, desc, count, delta, timestamp }` |
| `GET /v1/batch/products` | 产品持仓 | `Product { id, name, code, beforeAmt, afterAmt, cash, deviation, flagged, bonds[] }` |

### 4.6 门户大盘 (MapPortal)

| 建议接口 | 用途 | 关键数据结构 |
|---------|------|-------------|
| `GET /v1/portal/market-trend` | 市场走势 | `{ time, value }[]` |
| `GET /v1/portal/deviation` | 偏离度数据 | `{ label, value, color }[]` |
| `GET /v1/portal/performance` | 业绩走势 | `{ month, series1, series2, ... }[]` |

---

## 五、枚举值与业务映射

### 5.1 角色映射（前端 → 后端 Query 参数）

| 前端 `activeRole` | 后端 `role` 参数 | 说明 |
|-------------------|-----------------|------|
| `投资经理` | `PM` | 默认 |
| `班子` | `LEADERSHIP` | |
| `部门长` | `DEPT_HEAD` | |
| `风控合规总监` | `RISK` | |
| `秘书` | `SECRETARY` | |
| `主任委员` | `CHAIRMAN` | |
| `FICC投资委员会主任委员` | `FICC_CHAIRMAN` | |
| `FICC投资委员会秘书` | `FICC_SECRETARY` | |
| `FICC投资委员会委员` | `FICC_MEMBER` | |

### 5.2 资产评分映射

| 评分值 | 含义 | 前端颜色 |
|--------|------|---------|
| 1 | 极度看空 | `#FF3B30` |
| 2 | 偏空 | `#FF6B00` |
| 3 | 中性 | `#94A3B8` |
| 4 | 偏多 | `#3B9EFF` |
| 5 | 极度看多 | `#34C759` |

### 5.3 choice_items 值映射

| 后端值 | 中文含义 | 前端颜色 |
|--------|---------|---------|
| `underweight` | 低配 | `#FF3B30` |
| `neutral` | 中性 | `#94A3B8` |
| `overweight` | 超配 | `#34C759` |

### 5.4 会议状态流转

```
待召开 → 进行中 → 已结束 → 已归档
                  ↘ 已取消
```

### 5.5 FICC 投票维度

| 维度 Key | 中文 | 取值范围 | 颜色 |
|----------|------|---------|------|
| `position` | 稳定资产仓位 | 0-100 % | `#3B9EFF` |
| `duration` | 久期使用率 | 0-100 % | `#22D3EE` |
| `equity` | 含权使用率 | 0-100 % | `#8B5CF6` |

### 5.6 FICC 久期选项

| 值 | 含义 |
|----|------|
| `短久期` | Short duration |
| `中短久期` | Medium-short |
| `中长久期` | Medium-long |

### 5.7 纪要状态 (MinuteState)

| 值 | 含义 | 前端行为 |
|----|------|---------|
| `draft` | 草稿 | 显示"生成纪要"按钮 |
| `pending` | 生成中 | 显示 loading + 打字机效果 |
| `ready` | 已就绪 | 显示完整纪要 + 签发按钮 |

---

## 六、WebSocket / SSE 依赖

### 6.1 AI 纪要生成（打字机效果）

**当前实现**: 前端使用 `setTimeout` 逐条显示硬编码的纪要要点，模拟打字机效果。

**建议后端实现**: 改为 **SSE (Server-Sent Events)** 流式输出。

| 项目 | 说明 |
|------|------|
| **建议 Endpoint** | `GET /v1/committee/minutes/stream?meeting_id={id}` |
| **Content-Type** | `text/event-stream` |
| **事件格式** | SSE 标准 `data: {...}\n\n` |

**前端期望的 SSE 事件数据**:
```jsonc
// 逐条推送纪要要点
data: { "type": "point", "index": 0, "text": "权益维持中性配置..." }

// 推送完毕
data: { "type": "done", "fullText": "## 会议纪要\n\n..." }
```

**触发场景**: 
- 混合投委会 Tab 4（会议纪要与归档）的"生成纪要"按钮
- FICC 投委会 Tab 4 的"生成纪要"按钮

### 6.2 录音功能

**当前实现**: 纯前端模拟（`setInterval` 生成波形数据），无实际录音 API。

**后端无需支持**: 此功能为前端本地行为，暂不需要后端接口。

---

## 附录：接口优先级建议

| 优先级 | 接口 | 理由 |
|--------|------|------|
| **P0** | 会议 CRUD (1.1, 1.2, 1.3) | 核心业务流程入口 |
| **P0** | 问卷提交/查询 (1.4, 1.7) | 委员投票核心链路 |
| **P0** | 页面上下文 (3.2) | 投委会页面初始化必需 |
| **P1** | 门户快照 (3.1) | 大盘/决议表共享 |
| **P1** | FICC 全套 (2.1~2.10) | FICC 模块数据源 |
| **P2** | 历史评分 (1.5) | 图表展示，非核心 |
| **P2** | 催办 (1.6) | 体验优化 |
| **P3** | AI 纪要 SSE (6.1) | 高级功能，可后补 |
| **P3** | 终端/模型/因子 (4.x) | 独立模块，可并行开发 |
