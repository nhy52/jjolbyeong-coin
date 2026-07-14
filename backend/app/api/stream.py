"""SSE 스트림 엔드포인트.

클라이언트는 로그인 후 이 엔드포인트를 EventSource로 구독한다.
서버는 이벤트 버스에서 해당 사용자에게 라우팅된 이벤트를 실시간으로 흘려보낸다.

⚠️ PoC 단계: 사용자 식별을 query param(user_id, group_id, role)으로 받는다.
   추후 JWT 인증으로 교체 예정(기획서 인증 섹션).
"""

from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Query, Request
from sse_starlette.sse import EventSourceResponse

from app.events.bus import bus

router = APIRouter()

# 연결 유지를 위한 heartbeat 주기(초). 프록시 타임아웃 방지.
HEARTBEAT_SECONDS = 20


@router.get("/stream")
async def stream(
    request: Request,
    user_id: int = Query(...),
    group_id: int | None = Query(None),
    role: str = Query("minion"),
):
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
