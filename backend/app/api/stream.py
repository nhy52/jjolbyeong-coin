"""SSE 스트림 엔드포인트.

클라이언트는 로그인 후 이 엔드포인트를 EventSource로 구독한다.
서버는 이벤트 버스에서 해당 사용자에게 라우팅된 이벤트를 실시간으로 흘려보낸다.

인증: EventSource는 헤더를 못 실으므로 access token을 query(`token`)로 받는다.
     토큰이 있으면 이를 신뢰하고, 없으면 데모용 query param(user_id 등)으로 폴백한다.
"""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, HTTPException, Query, Request, status
from sse_starlette.sse import EventSourceResponse

from app.core.security import decode_token_safe
from app.events.bus import bus

router = APIRouter()

# 연결 유지를 위한 heartbeat 주기(초). 프록시 타임아웃 방지.
HEARTBEAT_SECONDS = 20


@router.get("/stream")
async def stream(
    request: Request,
    token: str | None = Query(None),
    user_id: int | None = Query(None),
    group_id: int | None = Query(None),
    role: str = Query("minion"),
):
    if token is not None:
        payload = decode_token_safe(token)
        if payload is None or payload.get("typ") != "access":
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "유효하지 않은 토큰입니다.")
        user_id = int(payload["sub"])
        group_id = payload.get("gid")
        role = payload.get("role", "minion")
    elif user_id is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "token 또는 user_id가 필요합니다.")

    sub = await bus.subscribe(user_id=user_id, group_id=group_id, role=role)

    async def event_generator():
        try:
            # 연결 직후 준비 완료 신호
            yield {"event": "ready", "data": json.dumps({"type": "ready"})}
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(
                        sub.queue.get(), timeout=HEARTBEAT_SECONDS
                    )
                    yield {
                        "event": event.get("type", "message"),
                        "data": json.dumps(event, ensure_ascii=False),
                    }
                except asyncio.TimeoutError:
                    # heartbeat (comment ping) — 연결 유지용
                    yield {"event": "ping", "data": "{}"}
        finally:
            await bus.unsubscribe(sub)

    return EventSourceResponse(event_generator())
