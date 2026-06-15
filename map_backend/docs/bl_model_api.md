# BL 模型接口文档

## 接口 1：获取会议投票统计

**路径：** `POST /api/v1/committee/meetings/vote-config`

**功能：** 统计指定会议下所有投票记录的 `section_a`（资产评分），按资产聚合各评分的票数。

### 请求参数

| 参数 | 位置 | 类型 | 必填 | 说明 |
|------|------|------|------|------|
| meeting_id | body | int | 是 | 会议 ID |

### 请求示例

```json
{
  "meeting_id": 123
}
```

### 响应

```json
{
  "固收-存单": {"3": 8, "4": 1},
  "固收-信用": {"3": 6, "4": 3},
  "固收-利率10Y": {"3": 8, "4": 1},
  "固收-利率30Y": {"3": 7, "4": 2, "5": 1},
  "含权-转债": {"2": 1, "3": 5, "4": 3},
  "含权-二级债基": {"3": 8, "4": 2},
  "含权-红利": {"3": 6, "4": 4},
  "含权-偏股混": {"2": 1, "3": 5, "4": 3},
  "含权-恒生科技": {"2": 2, "3": 2, "4": 6},
  "另类-黄金": {"3": 2, "4": 8}
}
```

### 错误码

| 状态码 | 说明 |
|--------|------|
| 404 | 会议不存在或已删除 |
| 422 | 请求体格式错误 |

---

## 接口 2：调用 Lighthouse BL 模型

**路径：** `POST /api/v1/committee/lighthouse/run`

**功能：** 将投票统计发送给 Lighthouse 平台的 Black-Litterman 模型，返回三份 HTML 报告（summary_low.html / summary_medium.html / summary_fix.html）和 weights 数据。

### 请求参数

请求体为 JSON，支持三种使用模式：

#### 模式 A：从数据库自动读取（推荐）

```json
{
  "meeting_id": 123
}
```

从数据库读取该会议的投票记录（聚合为 vote_config）和 scheduled_at（作为 meeting_date）。

#### 模式 B：完全手动传入

```json
{
  "meeting_date": "20260507",
  "vote_config": {
    "固收-存单": {"3": 8, "4": 1},
    "含权-红利": {"3": 6, "4": 4}
  }
}
```

不传 `meeting_id` 时，`meeting_date` 和 `vote_config` 均为必填。

#### 模式 C：传入 meeting_id 但覆盖 meeting_date

```json
{
  "meeting_id": 123,
  "meeting_date": "20260507"
}
```

`meeting_date` 优先级：入参 > 数据库 scheduled_at。

### 请求体字段说明

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| meeting_id | int | 否 | 会议 ID。传入则从数据库自动读取投票记录和日期 |
| meeting_date | string | 条件必填 | 会议日期，格式 `YYYYMMDD`。不传 meeting_id 时必填 |
| vote_config | object | 条件必填 | 投票统计，key 为资产名，value 为各评分的票数。不传 meeting_id 时必填 |

### 响应

```json
{
  "html_files": [
    {
      "file_name": "summary_low.html",
      "content": "<base64 编码的 HTML 内容>"
    },
    {
      "file_name": "summary_medium.html",
      "content": "<base64 编码的 HTML 内容>"
    },
    {
      "file_name": "summary_fix.html",
      "content": "<base64 编码的 HTML 内容>"
    }
  ],
  "weights": [
    {
      "大类": "固收-存单",
      "w_mkt": "0.05",
      "w_star": "0.06",
      "delta": "0.01",
      "mu_BL": "0.03"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| html_files | array | 三个 HTML 报告文件，每个包含 `file_name` 和 `content`（base64 编码） |
| weights | array | weights.csv 解析后的 JSON 数组，每行一个对象 |

### 错误码

| 状态码 | 说明 |
|--------|------|
| 400 | meeting_date 和 vote_config 均未传入（不传 meeting_id 时） |
| 404 | 会议不存在或已删除 |
| 422 | 请求体格式错误 |
| 500 | Lighthouse 任务执行失败或返回文件为空 |

### 处理流程

1. 确定 `meeting_date` 和 `vote_config`（从数据库或入参）
2. 调用 Lighthouse 平台发起任务（POST + 轮询）
3. 轮询任务状态直到完成（最长 60 秒，间隔 2 秒）
4. 下载返回的文件：`summary_*.csv` 转为 `summary_*.html`（base64 编码），`weights.csv` 解析为 JSON

### 注意事项

- 该接口调用外部 Lighthouse 平台，依赖网络连通性
- 轮询超时时间为 60 秒，超时后抛出错误
- `content` 字段为 base64 编码，前端需解码后使用
