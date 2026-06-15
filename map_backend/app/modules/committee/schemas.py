"""
modules/committee/schemas.py — Pydantic V2 Request / Response 模型
枚举类型从 models.py 统一导入，避免两套常量漂移。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field

from app.modules.committee.models import MeetingStatus, MeetingType


# ── Request Schemas ───────────────────────────────────────────────────────────


class CreateMeetingRequest(BaseModel):
    meeting_code: str = Field(..., min_length=1, max_length=64, description="会议编码（全局唯一）")
    title: str = Field(..., min_length=1, max_length=256, description="会议标题")
    type: MeetingType = Field(..., description="会议类型 mixed / ficc")
    scheduled_at: datetime | None = Field(None, description="计划召开时间（可选）")


class SubmitVoteRequest(BaseModel):
    """
    投票提交请求（对齐 API 文档 §3.6 扁平结构）。
    两套投委会共用，通过 committee_type 区分。
    """

    committee_type: Literal["mixed", "ficc"] = Field(
        ..., description="投委会类型"
    )
    vote_dimension: Literal["monthly", "quarterly"] = Field(
        default="monthly", description="投票维度：mixed 固定传 monthly"
    )

    # ── 混合投委会资产评分（Section A）─────────────────────────────────────
    section_a: dict[str, int] | None = Field(
        None,
        description="资产评分，key=资产名，value=1~5 整数档位",
        examples=[{"红利": 4, "偏股混": 3, "恒生科技": 5}],
    )

    # ── 创新高预判（Section B）─────────────────────────────────────────────
    section_b: dict[str, bool] | None = Field(
        None,
        description="创新高预判，key=资产名，value=boolean",
    )

    # ── 重点资产标记（Section C）───────────────────────────────────────────
    section_c: list[str] | None = Field(
        None,
        description="重点关注的资产名称列表",
        examples=[["利率债", "黄金"]],
    )

    # ── 委员综合市场观点 ────────────────────────────────────────────────────
    core_view: str | None = Field(None, description="委员综合市场观点")

    # ── 风险提示标记 ────────────────────────────────────────────────────────
    risk_flag: bool | None = Field(None, description="风险提示标记")

    # ── FICC 专有扩展字段 ───────────────────────────────────────────────────
    ficc_position_pct: float | None = Field(None, description="稳定资产仓位比例 0~100")
    ficc_duration_pct: float | None = Field(None, description="久期使用率 0~100")
    ficc_equity_pct: float | None = Field(None, description="穿透含权率 0~100")

    # ── 代填模式字段 ────────────────────────────────────────────────────────
    target_member_id: int | None = Field(None, description="被代填委员 user_id")
    is_proxy: bool | None = Field(None, description="是否代填提交")
    proxy_submitter_role: str | None = Field(None, description="代填人角色")


# ── Response Schemas ──────────────────────────────────────────────────────────


class MeetingResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    meeting_code: str
    title: str
    type: MeetingType
    status: MeetingStatus
    scheduled_at: datetime | None
    created_by: int
    created_at: datetime
    updated_at: datetime


class VoteRecordResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    meeting_id: int
    user_id: int
    vote_json: dict[str, Any]
    numeric_items: dict[str, Any] | None = None
    committee_type: str | None = None
    vote_dimension: str | None = None
    submitted_at: datetime | None
    created_at: datetime


# ── 聚合结果子结构 ────────────────────────────────────────────────────────────


class ChoiceAggregation(BaseModel):
    """单个分类题的众数聚合结果。"""

    winner: str = Field(description="得票最多的选项")
    vote_counts: dict[str, int] = Field(description="各选项得票数")


class NumericAggregation(BaseModel):
    """单个点位题的均值聚合结果。"""

    mean: float = Field(description="算术均值")
    std: float | None = Field(None, description="标准差（样本≥2时计算）")
    min: float = Field(description="最小值")
    max: float = Field(description="最大值")
    count: int = Field(description="有效投票数")


class ResolutionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    meeting_id: int
    aggregated_taa: dict[str, Any] = Field(
        description="聚合决议 JSON，含 choice_results 与 numeric_results"
    )
    ai_minutes: str | None = Field(None, description="AI 生成会议纪要")
    published_at: datetime | None
    published_by: int | None
    created_at: datetime


class PublishResponse(BaseModel):
    """发布决议的聚合响应：同时返回更新后的会议状态与决议内容。"""

    meeting: MeetingResponse
    resolution: ResolutionResponse


class CommitteeVoteRow(BaseModel):
    """投委会页上下文中的单条投票摘要（不含 vote_json 全文，避免 payload 过大）。"""

    user_id: int
    submitted_at: datetime | None


class CommitteePageContextResponse(BaseModel):
    """
    投委会视图首屏只读上下文：最近一次已发布决议 + 会议元数据 + 本场投票提交列表。
    无数据时各字段为 null / 空数组，前端应降级展示 Mock 占位。
    """

    meeting: MeetingResponse | None = None
    resolution: ResolutionResponse | None = None
    votes: list[CommitteeVoteRow] = Field(default_factory=list)


# ── 主任委员资配决议 ─────────────────────────────────────────────────────────


class EquityMix(BaseModel):
    红利: float = Field(description="红利 %")
    成长: float = Field(description="成长 %")
    价值: float = Field(description="价值 %")


class ProductGuidance(BaseModel):
    product_id: str = Field(description="产品标识: low / mid / hybrid")
    product_name: str = Field(description="产品名称")
    bond_grade: str = Field(description="固收久期档位")
    bond_pct: float = Field(description="固收仓位 %")
    equity_pct: float = Field(description="权益总仓位 %")
    equity_sub: dict[str, float] = Field(description="权益子项分配")
    alt_pct: float = Field(description="另类 %")
    liquidity_pct: float = Field(description="流动性 %")


class ChairResolutionRequest(BaseModel):
    """主任委员资配决议请求（对齐 API 文档 §3.8）。"""

    bond_grade: Literal["高", "中", "低"] = Field(description="固收久期档位")
    bond_duration: str = Field(description="固收久期区间，如 3-7年")
    equity_grade: int = Field(..., ge=1, le=5, description="权益档位 1~5")
    equity_grade_label: str = Field(description="权益档位中文标签")
    equity_mix: EquityMix | None = Field(None, description="权益明细分配")
    alt_notes: str | None = Field(None, description="另类资产备注")
    products: list[ProductGuidance] | None = Field(None, description="三类产品指引")


class ChairResolutionResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    meeting_id: int
    resolution_id: int | None = None
    bond_grade: str
    bond_duration: str
    equity_grade: int
    equity_grade_label: str
    equity_mix: dict[str, Any] | None = None
    alt_notes: str | None = None
    products: dict[str, Any] | None = None
    created_at: datetime


# ── 混合投委会会话查询 ──────────────────────────────────────────────────────


class MixedSessionSubmission(BaseModel):
    """单个委员的问卷提交记录。"""

    submitter_id: int
    submitted_at: str | None
    questionnaire_json: dict[str, Any]


class MixedSessionsResponse(BaseModel):
    """GET /mixed/sessions 响应。"""

    submissions: list[MixedSessionSubmission]


class SessionScoreStats(BaseModel):
    """单个资产的历史评分统计。"""

    avg: float
    max: float
    min: float
    count: int


class HistoricalSession(BaseModel):
    """单场历史会期的评分汇总。"""

    session_code: str
    submitted_count: int
    scores: dict[str, SessionScoreStats]


class MixedSessionsHistoryResponse(BaseModel):
    """GET /mixed/sessions/history 响应。"""

    sessions: list[HistoricalSession]


class RemindRequest(BaseModel):
    """POST /mixed/remind 请求。"""

    member_name: str
    member_id: int | None = None


class VoteConfigRequest(BaseModel):
    """POST /meetings/{meeting_id}/vote-config 请求。"""

    meeting_id: int = Field(..., description="会议 ID")


class LighthouseModelRequest(BaseModel):
    """POST /lighthouse/run 请求。"""

    meeting_id: int | None = Field(None, description="会议 ID。传入则从数据库读取投票记录和日期")
    meeting_date: str | None = Field(None, description="会议日期，格式 YYYYMMDD。不传 meeting_id 时必填")
    vote_config: dict[str, dict[str, int]] | None = Field(
        None,
        description="投票统计。不传 meeting_id 时必填，格式如 {'固收-存单': {'3': 8, '4': 1}}",
    )
