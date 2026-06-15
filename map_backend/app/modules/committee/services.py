"""
modules/committee/services.py — 投委会业务逻辑层

层次职责划分：
  ┌─ 纯函数区（无 I/O，可直接单元测试） ──────────────────────────────────────┐
  │  _score_to_vote_choice()  1~5 分数 → overweight/neutral/underweight       │
  │  _compute_mode()          分类选择题 → 众数                               │
  │  _compute_numeric_stats() 数值点位题 → 均值 / 标准差 / 极值               │
  │  _aggregate_votes()       整合两类计算，生成 aggregated_taa dict          │
  └───────────────────────────────────────────────────────────────────────────┘
  ┌─ 服务函数区（async，协调 DB I/O 与领域逻辑） ──────────────────────────────┐
  │  create_meeting()                                                         │
  │  list_meetings()          支持按 type 筛选                                │
  │  delete_meeting()         软删除                                          │
  │  submit_vote()            幂等提交（覆盖已有投票）                         │
  │  aggregate_ficc_resolution()  核心计票聚合 + 发布决议                     │
  └───────────────────────────────────────────────────────────────────────────┘
"""
import asyncio
import csv
import json
import statistics
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleException, NotFoundException
from app.modules.committee.models import (
    IcChairResolution,
    IcMeeting,
    IcResolution,
    IcVoteRecord,
    MeetingStatus,
    MeetingType,
)
from app.modules.committee.schemas import (
    ChairResolutionRequest,
    CommitteePageContextResponse,
    CommitteeVoteRow,
    CreateMeetingRequest,
    HistoricalSession,
    MeetingResponse,
    MixedSessionSubmission,
    MixedSessionsHistoryResponse,
    MixedSessionsResponse,
    RemindRequest,
    ResolutionResponse,
    SessionScoreStats,
    SubmitVoteRequest,
)


# ══════════════════════════════════════════════════════════════════════════════
#  纯函数区 — 零外部依赖，零 I/O，极易单元测试
# ══════════════════════════════════════════════════════════════════════════════


def _score_to_vote_choice(score: int) -> str:
    """1~5 档位分数 → overweight / neutral / underweight（对齐前端 scoreToVoteChoice）。"""
    if score <= 2:
        return "underweight"
    if score >= 4:
        return "overweight"
    return "neutral"


def _compute_mode(values: list[str]) -> tuple[str, dict[str, int]]:
    """
    对字符串列表求众数。

    Returns:
        (winner, vote_counts)
        winner: 得票最多的选项；若首位平票则取字典序第一个（保证确定性）。
        vote_counts: 全部选项的得票统计。
    """
    if not values:
        raise ValueError("_compute_mode: 输入列表为空")
    counter = Counter(values)
    max_count = counter.most_common(1)[0][1]
    tied_winners = sorted(k for k, v in counter.items() if v == max_count)
    return tied_winners[0], dict(counter)


def _compute_numeric_stats(values: list[float]) -> dict[str, Any]:
    """
    对数值列表计算统计指标（均值 / 标准差 / 最大 / 最小 / 个数）。
    标准差在样本数 < 2 时为 None（无统计意义）。
    """
    if not values:
        raise ValueError("_compute_numeric_stats: 输入列表为空")
    return {
        "mean": statistics.mean(values),
        "std": statistics.stdev(values) if len(values) >= 2 else None,
        "min": min(values),
        "max": max(values),
        "count": len(values),
    }


def _aggregate_votes(
    vote_records: list[IcVoteRecord],
    meeting_type: MeetingType,
) -> dict[str, Any]:
    """
    混合 / FICC 核心计票算法（纯函数）：

    算法规则
    --------
    - section_a 各资产评分（1~5 整数）→ 按 scoreToVoteChoice 映射为 overweight/neutral/underweight → **众数 (Mode)**
    - numeric_items → 逐 key 收集所有委员的数值预测 → **均值 (Mean)**

    容错机制
    --------
    - 若某委员未填写某 key，跳过该条目（不参与该 key 的统计）

    Returns:
        aggregated_taa dict，可直接写入 IcResolution.aggregated_taa
    """
    if not vote_records:
        raise BusinessRuleException("无有效投票记录，无法生成决议")

    # 按 key 分桶
    choice_buckets: dict[str, list[str]] = {}
    numeric_buckets: dict[str, list[float]] = {}

    for record in vote_records:
        vote_data: dict = record.vote_json or {}

        # section_a: {资产名: 1~5 整数} → 转为 overweight/neutral/underweight
        section_a: dict = vote_data.get("section_a", {})
        for asset_name, score in section_a.items():
            try:
                mapped = _score_to_vote_choice(int(score))
                choice_buckets.setdefault(asset_name, []).append(mapped)
            except (TypeError, ValueError):
                pass

        # numeric_items: {key: number}
        num_items: dict = record.numeric_items or {}
        for key, val in num_items.items():
            try:
                numeric_buckets.setdefault(key, []).append(float(val))
            except (TypeError, ValueError):
                pass

    # 计算众数
    choice_results: dict[str, Any] = {}
    for key, values in choice_buckets.items():
        winner, counts = _compute_mode(values)
        choice_results[key] = {
            "winner": winner,
            "vote_counts": counts,
        }

    # 计算均值
    numeric_results: dict[str, Any] = {}
    for key, values in numeric_buckets.items():
        numeric_results[key] = _compute_numeric_stats(values)

    return {
        "meeting_type": meeting_type.value,
        "total_voters": len(vote_records),
        "computed_at": datetime.now(timezone.utc).isoformat(),
        "choice_results": choice_results,
        "numeric_results": numeric_results,
    }


# ══════════════════════════════════════════════════════════════════════════════
#  服务函数区 — 异步，协调 DB I/O 与领域逻辑
# ══════════════════════════════════════════════════════════════════════════════


async def _fetch_active_meeting(db: AsyncSession, meeting_id: int) -> IcMeeting:
    """通用查询：获取未软删除的会议；不存在则抛 NotFoundException。"""
    stmt = select(IcMeeting).where(
        IcMeeting.id == meeting_id,
        IcMeeting.is_deleted == 0,
    )
    meeting = (await db.execute(stmt)).scalar_one_or_none()
    if meeting is None:
        raise NotFoundException(f"会议 {meeting_id} 不存在或已删除")
    return meeting


async def create_meeting(
    db: AsyncSession,
    payload: CreateMeetingRequest,
    user_id: int,
) -> IcMeeting:
    """
    创建一场新会议，初始状态为 draft。
    meeting_code 唯一索引由数据库兜底；若重复将抛 IntegrityError（由全局处理器转化为 409）。
    """
    meeting = IcMeeting(
        meeting_code=payload.meeting_code,
        title=payload.title,
        type=MeetingType(payload.type.value),
        status=MeetingStatus.DRAFT,
        scheduled_at=payload.scheduled_at,
        created_by=user_id,
    )
    db.add(meeting)
    await db.flush()
    await db.refresh(meeting)
    return meeting


async def list_meetings(
    db: AsyncSession,
    meeting_type: str | None = None,
) -> list[IcMeeting]:
    """按创建时间倒序返回未软删除的会议列表。可按 type 筛选。"""
    stmt = (
        select(IcMeeting)
        .where(IcMeeting.is_deleted == 0)
        .order_by(IcMeeting.created_at.desc())
    )
    if meeting_type is not None:
        try:
            mt = MeetingType(meeting_type)
            stmt = stmt.where(IcMeeting.type == mt)
        except ValueError:
            pass  # 无效值忽略，返回全部
    return list((await db.execute(stmt)).scalars().all())


async def delete_meeting(db: AsyncSession, meeting_id: int) -> None:
    """软删除会议：将 is_deleted 置为 1。"""
    meeting = await _fetch_active_meeting(db, meeting_id)
    meeting.is_deleted = 1
    await db.flush()


async def submit_vote(
    db: AsyncSession,
    meeting_id: int,
    user_id: int,
    payload: SubmitVoteRequest,
) -> IcVoteRecord:
    """
    提交或覆盖投票（幂等设计）。

    状态机副作用：
      draft  → 自动推进到 voting（首票到达时打开投票窗口）
      voting → 正常接受投票
      published → 拒绝（终态保护）

    幂等性：同一 (meeting_id, user_id) 再次提交将覆盖，不新建记录。
    代填模式：payload.target_member_id 有值时，投票记在该委员名下。
    """
    meeting = await _fetch_active_meeting(db, meeting_id)

    if meeting.status == MeetingStatus.PUBLISHED:
        raise BusinessRuleException("会议已发布决议，投票窗口已关闭")

    # 首票到达，推进状态
    if meeting.status == MeetingStatus.DRAFT:
        meeting.status = MeetingStatus.VOTING

    now = datetime.now(timezone.utc)

    # 构建存储 JSON
    vote_json: dict[str, Any] = {}
    if payload.section_a is not None:
        vote_json["section_a"] = payload.section_a
    if payload.section_b is not None:
        vote_json["section_b"] = payload.section_b
    if payload.section_c is not None:
        vote_json["section_c"] = payload.section_c
    if payload.core_view is not None:
        vote_json["core_view"] = payload.core_view
    if payload.risk_flag is not None:
        vote_json["risk_flag"] = payload.risk_flag

    # 构建 numeric_items JSON
    numeric_items: dict[str, float] = {}
    if payload.ficc_position_pct is not None:
        numeric_items["ficc_position_pct"] = payload.ficc_position_pct
    if payload.ficc_duration_pct is not None:
        numeric_items["ficc_duration_pct"] = payload.ficc_duration_pct
    if payload.ficc_equity_pct is not None:
        numeric_items["ficc_equity_pct"] = payload.ficc_equity_pct

    # 代填模式：target_member_id 替代 user_id
    effective_user_id = payload.target_member_id if payload.is_proxy and payload.target_member_id else user_id

    # 幂等查询：优先查活跃记录
    existing_stmt = select(IcVoteRecord).where(
        IcVoteRecord.meeting_id == meeting_id,
        IcVoteRecord.user_id == effective_user_id,
        IcVoteRecord.is_deleted == 0,
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()

    if existing:
        existing.vote_json = vote_json
        existing.numeric_items = numeric_items
        existing.committee_type = payload.committee_type
        existing.vote_dimension = payload.vote_dimension
        existing.submitted_at = now
        await db.flush()
        await db.refresh(existing)
        return existing

    # 查找软删除记录并恢复（避免唯一索引冲突）
    soft_deleted_stmt = select(IcVoteRecord).where(
        IcVoteRecord.meeting_id == meeting_id,
        IcVoteRecord.user_id == effective_user_id,
        IcVoteRecord.is_deleted == 1,
    )
    soft_deleted = (await db.execute(soft_deleted_stmt)).scalar_one_or_none()
    if soft_deleted:
        soft_deleted.is_deleted = 0
        soft_deleted.vote_json = vote_json
        soft_deleted.numeric_items = numeric_items
        soft_deleted.committee_type = payload.committee_type
        soft_deleted.vote_dimension = payload.vote_dimension
        soft_deleted.submitted_at = now
        await db.flush()
        await db.refresh(soft_deleted)
        return soft_deleted

    record = IcVoteRecord(
        meeting_id=meeting_id,
        user_id=effective_user_id,
        vote_json=vote_json,
        numeric_items=numeric_items,
        committee_type=payload.committee_type,
        vote_dimension=payload.vote_dimension,
        submitted_at=now,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


async def aggregate_ficc_resolution(
    db: AsyncSession,
    meeting_id: int,
    publisher_id: int,
) -> tuple[IcMeeting, IcResolution]:
    """
    计票聚合并发布决议（服务主入口）。

    执行步骤
    --------
    1. 校验会议存在且处于 voting 状态（draft 未投票 / published 终态均拒绝）
    2. 读取全部有效投票记录（is_deleted = 0）
    3. 调用纯函数 _aggregate_votes() 完成众数 / 均值计算
    4. Upsert IcResolution（允许在发布前重新聚合，覆盖旧结果）
    5. 将会议状态推进到 published（终态，不可回滚）

    Returns:
        (updated_meeting, upserted_resolution)
    """
    meeting = await _fetch_active_meeting(db, meeting_id)

    if meeting.status == MeetingStatus.DRAFT:
        raise BusinessRuleException("会议尚未开放投票（draft），无法发布决议")
    if meeting.status == MeetingStatus.PUBLISHED:
        raise BusinessRuleException("会议已发布决议，禁止重复操作")

    votes_stmt = select(IcVoteRecord).where(
        IcVoteRecord.meeting_id == meeting_id,
        IcVoteRecord.is_deleted == 0,
    )
    votes: list[IcVoteRecord] = list(
        (await db.execute(votes_stmt)).scalars().all()
    )

    if not votes:
        raise BusinessRuleException("当前无有效投票记录，无法生成决议")

    aggregated = _aggregate_votes(votes, meeting.type)

    res_stmt = select(IcResolution).where(
        IcResolution.meeting_id == meeting_id,
        IcResolution.is_deleted == 0,
    )
    resolution = (await db.execute(res_stmt)).scalar_one_or_none()
    now = datetime.now(timezone.utc)

    if resolution:
        resolution.aggregated_taa = aggregated
        resolution.published_at = now
        resolution.published_by = publisher_id
    else:
        resolution = IcResolution(
            meeting_id=meeting_id,
            aggregated_taa=aggregated,
            ai_minutes=None,
            published_at=now,
            published_by=publisher_id,
        )
        db.add(resolution)

    meeting.status = MeetingStatus.PUBLISHED

    await db.flush()
    await db.refresh(meeting)
    await db.refresh(resolution)
    return meeting, resolution


async def get_committee_page_context(
    db: AsyncSession,
    committee_type: str | None = None,
) -> CommitteePageContextResponse:
    """
    投委会视图：拉取最近决议及会议、投票摘要。
    支持 committee_type 过滤（mixed / ficc）。
    无记录时返回空壳。
    """
    stmt = (
        select(IcResolution, IcMeeting)
        .join(IcMeeting, IcMeeting.id == IcResolution.meeting_id)
        .where(
            IcResolution.is_deleted == 0,
            IcMeeting.is_deleted == 0,
        )
    )
    if committee_type is not None:
        try:
            mt = MeetingType(committee_type)
            stmt = stmt.where(IcMeeting.type == mt)
        except ValueError:
            pass

    stmt = stmt.order_by(IcResolution.id.asc()).limit(1)
    row = (await db.execute(stmt)).first()
    if row is None:
        return CommitteePageContextResponse()

    resolution, meeting = row

    votes_stmt = (
        select(IcVoteRecord)
        .where(
            IcVoteRecord.meeting_id == meeting.id,
            IcVoteRecord.is_deleted == 0,
        )
        .order_by(IcVoteRecord.submitted_at.desc())
    )
    vote_rows = list((await db.execute(votes_stmt)).scalars().all())

    return CommitteePageContextResponse(
        meeting=MeetingResponse.model_validate(meeting),
        resolution=ResolutionResponse.model_validate(resolution),
        votes=[
            CommitteeVoteRow(user_id=v.user_id, submitted_at=v.submitted_at)
            for v in vote_rows
        ],
    )


async def save_chair_resolution(
    db: AsyncSession,
    meeting_id: int,
    payload: ChairResolutionRequest,
) -> IcChairResolution:
    """
    保存主任委员最终资配决议。

    幂等设计：同一 meeting_id 重复提交将覆盖旧记录。
    """
    await _fetch_active_meeting(db, meeting_id)

    # 查找已有的决议
    existing_stmt = select(IcChairResolution).where(
        IcChairResolution.meeting_id == meeting_id,
        IcChairResolution.is_deleted == 0,
    )
    existing = (await db.execute(existing_stmt)).scalar_one_or_none()

    products_data = [p.model_dump() for p in payload.products] if payload.products else None
    equity_mix_data = payload.equity_mix.model_dump() if payload.equity_mix else None

    if existing:
        existing.bond_grade = payload.bond_grade
        existing.bond_duration = payload.bond_duration
        existing.equity_grade = payload.equity_grade
        existing.equity_grade_label = payload.equity_grade_label
        existing.equity_mix = equity_mix_data
        existing.alt_notes = payload.alt_notes
        existing.products = products_data
        await db.flush()
        await db.refresh(existing)
        return existing

    record = IcChairResolution(
        meeting_id=meeting_id,
        bond_grade=payload.bond_grade,
        bond_duration=payload.bond_duration,
        equity_grade=payload.equity_grade,
        equity_grade_label=payload.equity_grade_label,
        equity_mix=equity_mix_data,
        alt_notes=payload.alt_notes,
        products=products_data,
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


# ── 混合投委会会话查询 ──────────────────────────────────────────────────────


async def get_mixed_sessions(
    db: AsyncSession,
) -> MixedSessionsResponse:
    """
    返回当前活跃混合投委会会议的全部委员提交记录。
    自动选取最近一场 voting 或 draft 状态的 mixed 会议。
    """
    meeting_stmt = (
        select(IcMeeting)
        .where(
            IcMeeting.is_deleted == 0,
            IcMeeting.type == MeetingType.MIXED,
            IcMeeting.status.in_([MeetingStatus.VOTING, MeetingStatus.DRAFT]),
        )
        .order_by(IcMeeting.created_at.desc())
        .limit(1)
    )
    meeting = (await db.execute(meeting_stmt)).scalar_one_or_none()
    if meeting is None:
        return MixedSessionsResponse(submissions=[])

    votes_stmt = (
        select(IcVoteRecord)
        .where(
            IcVoteRecord.meeting_id == meeting.id,
            IcVoteRecord.is_deleted == 0,
        )
        .order_by(IcVoteRecord.submitted_at.desc())
    )
    votes = list((await db.execute(votes_stmt)).scalars().all())

    submissions = []
    for v in votes:
        vote_data: dict = v.vote_json or {}
        submitted_at_str: str | None = None
        if v.submitted_at:
            submitted_at_str = v.submitted_at.isoformat()

        questionnaire: dict[str, Any] = {}
        if "section_a" in vote_data:
            questionnaire["section_a"] = vote_data["section_a"]
        if "section_b" in vote_data:
            questionnaire["section_b"] = vote_data["section_b"]
        if "section_c" in vote_data:
            questionnaire["section_c"] = vote_data["section_c"]
        if "core_view" in vote_data:
            questionnaire["core_view"] = vote_data["core_view"]
        if "risk_flag" in vote_data:
            questionnaire["risk_flag"] = vote_data["risk_flag"]

        submissions.append(
            MixedSessionSubmission(
                submitter_id=v.user_id,
                submitted_at=submitted_at_str,
                questionnaire_json=questionnaire,
            )
        )

    return MixedSessionsResponse(submissions=submissions)


async def get_mixed_sessions_history(
    db: AsyncSession,
    limit: int = 10,
) -> MixedSessionsHistoryResponse:
    """
    返回已发布的混合投委会历史会期评分数据。
    从各已发布会议的投票记录中计算 section_a 各资产的均值/极值/计数。
    """
    meetings_stmt = (
        select(IcMeeting)
        .where(
            IcMeeting.is_deleted == 0,
            IcMeeting.type == MeetingType.MIXED,
            IcMeeting.status == MeetingStatus.PUBLISHED,
        )
        .order_by(IcMeeting.created_at.desc())
        .limit(limit)
    )
    meetings = list((await db.execute(meetings_stmt)).scalars().all())

    sessions: list[HistoricalSession] = []
    for m in meetings:
        votes_stmt = select(IcVoteRecord).where(
            IcVoteRecord.meeting_id == m.id,
            IcVoteRecord.is_deleted == 0,
        )
        votes = list((await db.execute(votes_stmt)).scalars().all())

        buckets: dict[str, list[float]] = {}
        for v in votes:
            section_a: dict = (v.vote_json or {}).get("section_a", {})
            for asset, score in section_a.items():
                try:
                    buckets.setdefault(asset, []).append(float(score))
                except (TypeError, ValueError):
                    pass

        scores: dict[str, SessionScoreStats] = {}
        for asset, vals in buckets.items():
            scores[asset] = SessionScoreStats(
                avg=round(statistics.mean(vals), 2),
                max=max(vals),
                min=min(vals),
                count=len(vals),
            )

        code = m.meeting_code
        sessions.append(
            HistoricalSession(
                session_code=code,
                submitted_count=len(votes),
                scores=scores,
            )
        )

    return MixedSessionsHistoryResponse(sessions=sessions)


async def send_remind(
    db: AsyncSession,
    payload: RemindRequest,
) -> dict[str, str]:
    """发送催办通知（桩实现：仅记录日志，后续对接消息中心）。"""
    return {"status": "ok", "message": f"已向 {payload.member_name} 发送催办通知"}


# ── BL 模型相关 ──────────────────────────────────────────────────────────────


async def get_meeting_vote_config(
    db: AsyncSession,
    meeting_id: int,
) -> dict[str, dict[str, int]]:
    """
    获取指定会议的投票统计（section_a 资产评分聚合）。

    从数据库读取该会议的所有有效投票记录，按资产和评分聚合票数。
    """
    await _fetch_active_meeting(db, meeting_id)

    votes_stmt = select(IcVoteRecord).where(
        IcVoteRecord.meeting_id == meeting_id,
        IcVoteRecord.is_deleted == 0,
    )
    votes: list[IcVoteRecord] = list(
        (await db.execute(votes_stmt)).scalars().all()
    )

    return aggregate_vote_config(votes)


def aggregate_vote_config(
    vote_records: list[IcVoteRecord],
) -> dict[str, dict[str, int]]:
    """
    统计指定会议下所有投票记录的 section_a（资产评分）。

    按资产聚合各评分的票数，例如：
        {"固收-存单": {"3": 8, "4": 1}}
    表示"固收-存单"资产评分为 3 的有 8 票，评分为 4 的有 1 票。
    """
    buckets: dict[str, dict[str, int]] = {}

    for record in vote_records:
        section_a: dict = (record.vote_json or {}).get("section_a", {})
        for asset_name, score in section_a.items():
            score_key = str(int(score))
            buckets.setdefault(asset_name, {})
            buckets[asset_name][score_key] = buckets[asset_name].get(score_key, 0) + 1

    return buckets


async def call_lighthouse_model(
    db: AsyncSession,
    meeting_id: int | None = None,
    meeting_date: str | None = None,
    vote_config: dict[str, dict[str, int]] | None = None,
) -> tuple[list[dict], list[dict]]:
    """
    调用 Lighthouse BL 模型，返回 HTML 文件列表和 weights.csv 的 JSON 数据。

    两种使用模式：
      模式 A（传 meeting_id）：从数据库读取投票记录和 scheduled_at
      模式 B（不传 meeting_id）：需要手动传入 meeting_date 和 vote_config

    流程：
      1. 确定 meeting_date 和 vote_config（数据库 or 入参）
      2. 发送给 Lighthouse 平台
      3. 轮询任务状态直到完成
      4. 下载文件：summary_low.html / summary_medium.html / summary_fix.html
         weights.csv → 解析为 JSON

    Returns:
        (html_files, weights_json)
        html_files: [{"file_name": "summary_fix.html", "content": <base64>}, ...]
        weights_json: weights.csv 解析后的 JSON 数组（每行一个 dict）
    """
    # 1. 确定 meeting_date 和 vote_config
    if meeting_id is not None:
        # 模式 A：从数据库读取
        meeting = await _fetch_active_meeting(db, meeting_id)

        if meeting_date:
            resolved_date = meeting_date
        elif meeting.scheduled_at is not None:
            resolved_date = meeting.scheduled_at.strftime("%Y%m%d")
        else:
            raise BusinessRuleException(
                f"会议 {meeting_id} 未设置 scheduled_at，且未传入 meeting_date 参数"
            )

        votes_stmt = select(IcVoteRecord).where(
            IcVoteRecord.meeting_id == meeting_id,
            IcVoteRecord.is_deleted == 0,
        )
        votes: list[IcVoteRecord] = list(
            (await db.execute(votes_stmt)).scalars().all()
        )

        if not votes:
            raise BusinessRuleException(f"会议 {meeting_id} 无有效投票记录")

        resolved_vote_config = aggregate_vote_config(votes)
    else:
        # 模式 B：完全使用入参
        if not meeting_date:
            raise BusinessRuleException("不传 meeting_id 时，meeting_date 为必填")
        if not vote_config:
            raise BusinessRuleException("不传 meeting_id 时，vote_config 为必填")

        resolved_date = meeting_date
        resolved_vote_config = vote_config

    # 2. 调用 Lighthouse 接口
    lighthouse_payload = {
        "meeting_date": resolved_date,
        "vote_config": resolved_vote_config,
    }

    config = {
        "appCode": "f7a94ef56bda481d897a7450d8361bf3",
        "operationType": "run",
    }
    config["args"] = json.dumps(lighthouse_payload, ensure_ascii=False)

    headers = {"currentLoginUsername": "SHIHONGYI344"}
    url = "http://pawm-pfp-83022-gateway.fat001.qa.pab.com.cn/data/agm/noRegister/callModel/601327f77528421b99c38bb23206ea7e"

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, json=config, headers=headers)
        response.raise_for_status()
        result = response.json()

    run_id = result["data"]

    # 4. 轮询查询
    polling_interval = 2
    max_retries = 30

    for attempt in range(1, max_retries + 1):
        config_query = {
            "appCode": "f7a94ef56bda481d897a7450d8361bf3",
            "operationType": "query",
            "runId": run_id,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=config_query, headers=headers)
            response.raise_for_status()
            poll_result = response.json()

        run_status = poll_result.get("data", {}).get("runStatus")

        if run_status == "SUCCESS":
            break
        elif run_status == "FAILED":
            raise RuntimeError("Lighthouse 任务执行失败")
        elif run_status == "PENDING":
            if attempt < max_retries:
                await asyncio.sleep(polling_interval)
            else:
                raise TimeoutError("Lighthouse 任务执行超时")
        else:
            if attempt < max_retries:
                await asyncio.sleep(polling_interval)
            else:
                raise RuntimeError(f"未知 Lighthouse 任务状态: {run_status}")
    else:
        raise TimeoutError("Lighthouse 轮询次数用尽")

    # 5. 下载并处理文件
    file_list = poll_result.get("data", {}).get("fileList", [])
    if not file_list:
        raise RuntimeError("Lighthouse 返回的文件列表为空")

    import base64

    html_files: list[dict] = []
    weights_json: list[dict] = []

    for file_info in file_list:
        original_filename = file_info.get("fileName")
        file_url = file_info.get("fileUrl")

        if not original_filename or not file_url:
            continue

        async with httpx.AsyncClient(timeout=30.0) as client:
            file_response = await client.get(file_url)
            file_response.raise_for_status()
            content = file_response.content

        # summary_ 开头的 csv 是 HTML 报告，转 base64
        if original_filename.startswith("summary_") and original_filename.endswith(".csv"):
            html_name = original_filename.replace(".csv", ".html")
            html_files.append({
                "file_name": html_name,
                "content": base64.b64encode(content).decode("ascii"),
            })
        elif original_filename == "weights.csv":
            content_str = content.decode("utf-8")
            reader = csv.DictReader(content_str.splitlines())
            weights_json = [dict(row) for row in reader]
        else:
            # 其他文件也按 HTML 保存
            html_files.append({
                "file_name": original_filename,
                "content": base64.b64encode(content).decode("ascii"),
            })

    return html_files, weights_json
