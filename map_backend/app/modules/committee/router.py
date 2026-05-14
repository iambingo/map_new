"""
modules/committee/router.py — 投委会决策模块 API 路由

端点清单
--------
  GET  /page-context                   投委会视图只读上下文（最近已发布决议 + 投票摘要）
  GET  /meetings                       会议列表（未软删除，支持 ?type= 筛选）
  POST /meetings                       创建会议（draft 状态）
  DELETE /meetings/{meeting_id}        软删除会议
  POST /meetings/{meeting_id}/submit-vote   提交 / 覆盖投票（幂等）
  POST /meetings/{meeting_id}/publish  触发计票聚合并发布决议
  GET  /mixed/sessions                 混合投委会问卷提交列表
  GET  /mixed/sessions/history         混合投委会历史评分
  POST /mixed/remind                   发送催办通知
"""
from fastapi import APIRouter, Query, Response, status

from app.dependencies import CurrentUserID, DBSession, PortalUserID
from app.modules.committee import services
from app.modules.committee.models import IcMeeting
from app.modules.committee.schemas import (
    ChairResolutionRequest,
    ChairResolutionResponse,
    CommitteePageContextResponse,
    CreateMeetingRequest,
    MeetingResponse,
    MixedSessionsHistoryResponse,
    MixedSessionsResponse,
    PublishResponse,
    RemindRequest,
    ResolutionResponse,
    SubmitVoteRequest,
    VoteRecordResponse,
)

router = APIRouter()


@router.get(
    "/page-context",
    response_model=CommitteePageContextResponse,
    summary="投委会视图只读上下文",
    description=(
        "供前端投委会 Tab 首屏使用：ic_resolutions 中 id 最小的一条决议、会议元数据、"
        "本场会议投票提交列表（不含 vote_json 全文）。\n\n"
        "无数据时返回空对象，不 404。鉴权与 POST 相同：使用 Portal 联调策略（开发环境可不带 Token）。"
    ),
)
async def get_committee_page_context(
    db: DBSession,
    _user_id: PortalUserID,
    committee_type: str | None = Query(
        None, description="mixed 或 ficc，不传返回默认（mixed）"
    ),
) -> CommitteePageContextResponse:
    return await services.get_committee_page_context(db, committee_type)


@router.post(
    "/meetings",
    response_model=MeetingResponse,
    status_code=201,
    summary="创建投委会会议",
    description=(
        "新建一场投委会会议，初始状态为 **draft**。\n\n"
        "`meeting_code` 全局唯一，重复提交将返回 409。"
    ),
)
async def create_meeting(
    body: CreateMeetingRequest,
    db: DBSession,
    user_id: PortalUserID,
) -> MeetingResponse:
    meeting = await services.create_meeting(db, body, user_id)
    return MeetingResponse.model_validate(meeting)


@router.get(
    "/meetings",
    response_model=list[MeetingResponse],
    summary="会议列表",
    description="返回全部未软删除的会议，按创建时间倒序排列。可通过 ?type=mixed/ficc 筛选。",
)
async def list_meetings(
    db: DBSession,
    _user_id: PortalUserID,
    type: str | None = Query(None, description="mixed 或 ficc，不传返回全部"),
) -> list[MeetingResponse]:
    meetings = await services.list_meetings(db, meeting_type=type)
    return [MeetingResponse.model_validate(m) for m in meetings]


@router.delete(
    "/meetings/{meeting_id}",
    status_code=204,
    summary="软删除会议",
    description="将会议 is_deleted 置为 1，不物理删除。仅创建者或秘书角色可执行。",
)
async def delete_meeting(
    meeting_id: int,
    db: DBSession,
    _user_id: PortalUserID,
) -> Response:
    await services.delete_meeting(db, meeting_id)
    return Response(status_code=204)


@router.post(
    "/meetings/{meeting_id}/submit-vote",
    response_model=VoteRecordResponse,
    status_code=200,
    summary="提交投票",
    description=(
        "委员提交本场会议的投票内容（幂等接口，允许覆盖）。\n\n"
        "- 首票提交时，会议状态自动从 `draft` 推进到 `voting`。\n"
        "- 决议已发布（`published`）后禁止再提交。\n\n"
        "`vote_json` 存储三段式投票（section_a/b/c），`numeric_items` 存储 FICC 专有数值。"
    ),
)
async def submit_vote(
    meeting_id: int,
    body: SubmitVoteRequest,
    db: DBSession,
    user_id: PortalUserID,
) -> VoteRecordResponse:
    record = await services.submit_vote(db, meeting_id, user_id, body)
    return VoteRecordResponse.model_validate(record)


@router.post(
    "/meetings/{meeting_id}/publish",
    response_model=PublishResponse,
    status_code=200,
    summary="触发计票聚合并发布决议",
    description=(
        "对处于 **voting** 状态的会议执行计票并发布决议（不可逆操作）。\n\n"
        "**计票规则**\n"
        "- `section_a` 各资产评分 → 按 1-2=underweight / 3=neutral / 4-5=overweight 映射后取众数\n"
        "- `numeric_items` → 各指标取算术均值\n\n"
        "响应中同时返回更新后的会议信息与完整决议内容。"
    ),
)
async def publish_meeting(
    meeting_id: int,
    db: DBSession,
    user_id: PortalUserID,
) -> PublishResponse:
    meeting, resolution = await services.aggregate_ficc_resolution(
        db, meeting_id, user_id
    )
    return PublishResponse(
        meeting=MeetingResponse.model_validate(meeting),
        resolution=ResolutionResponse.model_validate(resolution),
    )


@router.post(
    "/meetings/{meeting_id}/resolution",
    response_model=ChairResolutionResponse,
    status_code=201,
    summary="保存主任委员资配决议",
    description=(
        "持久化主任委员在配置指引 Tab 确认的最终部门资配决议。"
        "幂等设计：同一 meeting_id 重复提交将覆盖旧记录。"
    ),
)
async def save_chair_resolution(
    meeting_id: int,
    body: ChairResolutionRequest,
    db: DBSession,
    _user_id: PortalUserID,
) -> ChairResolutionResponse:
    record = await services.save_chair_resolution(db, meeting_id, body)
    return ChairResolutionResponse.model_validate(record)


# ── 混合投委会会话 ──────────────────────────────────────────────────────────


@router.get(
    "/mixed/sessions",
    response_model=MixedSessionsResponse,
    summary="混合投委会问卷提交列表",
    description="返回当前活跃混合投委会会议的全部委员提交记录（含问卷 JSON）。",
)
async def get_mixed_sessions(
    db: DBSession,
    _user_id: PortalUserID,
) -> MixedSessionsResponse:
    return await services.get_mixed_sessions(db)


@router.get(
    "/mixed/sessions/history",
    response_model=MixedSessionsHistoryResponse,
    summary="混合投委会历史评分",
    description="返回已发布的混合投委会历史会期评分统计（各资产均值/极值/计数）。",
)
async def get_mixed_sessions_history(
    db: DBSession,
    _user_id: PortalUserID,
    limit: int = Query(10, ge=1, le=50, description="返回会期数量上限"),
) -> MixedSessionsHistoryResponse:
    return await services.get_mixed_sessions_history(db, limit=limit)


@router.post(
    "/mixed/remind",
    summary="发送催办通知",
    description="向指定委员发送催办通知（当前为桩实现）。",
)
async def send_remind(
    body: RemindRequest,
    db: DBSession,
    _user_id: PortalUserID,
) -> dict[str, str]:
    return await services.send_remind(db, body)
