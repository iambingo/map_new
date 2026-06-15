"""
app/modules/auth/sso_router.py — 根路径路由 / 门户 SSO 回调
门户登录成功后将浏览器 302 到我方**根 URL**并附加 `?ssoTokenId=xxx`，
因此本路由挂在 `/`：携带 ssoTokenId 时走 SSO 回调，否则返回服务欢迎页。
"""
from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from starlette.status import HTTP_302_FOUND

from app.core.config import settings
from app.core.security import create_access_token
from app.dependencies import OptionalDB
from app.modules.auth import services

router = APIRouter()


@router.get(
    "/",
    summary="根路径 / 门户 SSO 回调",
    description=(
        "1. 不带 `ssoTokenId` 查询参数：返回服务欢迎页（HTML 或 JSON，按 Accept 头判定）。"
        "2. 带 `ssoTokenId` 查询参数：作为门户 SSO 回调处理，校验 token 后签发内部 JWT，"
        "通过 HttpOnly Cookie 返回前端，并 302 重定向到 `SSO_LOGIN_REDIRECT_URL`。"
    ),
    response_model=None,
    tags=["Root"],
)
async def root_or_sso_callback(
    request: Request,
    db: OptionalDB,
    sso_token_id: str | None = Query(
        default=None,
        alias="ssoTokenId",
        description="门户颁发的一次性 SSO Token ID；不携带时返回欢迎页",
    ),
) -> RedirectResponse | HTMLResponse | dict:
    # ── 分支 1：未携带 ssoTokenId，返回欢迎页 ──────────────────────────────────
    if not sso_token_id:
        accept = (request.headers.get("accept") or "").lower()
        if "text/html" in accept:
            return HTMLResponse(
                "<!DOCTYPE html><html lang=\"zh-CN\"><head><meta charset=\"utf-8\"/>"
                "<meta name=\"viewport\" content=\"width=device-width\"/><title>"
                f"{settings.APP_NAME}</title></head><body>"
                f"<h1>{settings.APP_NAME}</h1>"
                "<p>服务已运行。业务 HTTP 接口前缀：<code>/api/v1</code></p>"
                "<ul><li><a href=\"/docs\">API 文档（Swagger）</a></li>"
                "<li><a href=\"/health\">健康检查</a></li></ul>"
                "</body></html>"
            )
        return {
            "service": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "docs": "/docs",
            "health": "/health",
            "api_base": "/api/v1",
        }

    # ── 分支 2：携带 ssoTokenId，走 SSO 回调流程 ───────────────────────────────
    if db is None:
        return RedirectResponse(
            url=f"{settings.SSO_LOGIN_REDIRECT_URL}?error=service_unavailable",
            status_code=HTTP_302_FOUND,
        )

    # 1. 校验门户 token，获取用户信息
    portal_info = await services.validate_sso_token(sso_token_id)

    if not portal_info.user_id:
        return RedirectResponse(
            url=f"{settings.SSO_LOGIN_REDIRECT_URL}?error=invalid_token",
            status_code=HTTP_302_FOUND,
        )

    # 2. 查找或创建本地用户
    user = await services.find_or_create_user(db, portal_info.user_id, portal_info)

    # 检查用户状态
    services.check_user_status(user)

    # 3. 更新最后登录时间
    await services.update_last_login(db, user)

    # 4. 签发内部 JWT
    internal_token = create_access_token(
        subject=user.id,
        extra_claims={"username": user.username, "portal_id": user.portal_user_id},
    )

    # 5. 通过 HttpOnly Cookie 返回 JWT，重定向到前端
    response = RedirectResponse(url=settings.SSO_LOGIN_REDIRECT_URL, status_code=HTTP_302_FOUND)
    response.set_cookie(
        key="mapToken",
        value=internal_token,
        httponly=True,
        secure=settings.APP_ENV == "production",
        samesite="lax",
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        path="/",
    )
    return response
