"""인메모리 SSE 이벤트 버스.

단일 프로세스 기준의 pub/sub. 각 SSE 연결(구독자)마다 asyncio.Queue를 만들고,
이벤트를 사용자/그룹/전역 단위로 라우팅한다.

다중 워커·다중 인스턴스로 확장할 때는 이 계층을 Redis Pub/Sub으로 교체한다
(기획서 9.3 참고). API 코드는 publish_* 함수만 호출하므로 교체가 국소적이다.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any


@dataclass(eq=False)  # 객체 정체성(id) 기반 해시 → set에 담기 위함
class Subscriber:
    user_id: int
    group_id: int | None
    role: str
    queue: asyncio.Queue[dict[str, Any]] = field(default_factory=lambda: asyncio.Queue(maxsize=100))


class EventBus:
    def __init__(self) -> None:
        self._subscribers: set[Subscriber] = set()
        self._lock = asyncio.Lock()

    async def subscribe(self, user_id: int, group_id: int | None, role: str) -> Subscriber:
        sub = Subscriber(user_id=user_id, group_id=group_id, role=role)
        async with self._lock:
            self._subscribers.add(sub)
        return sub

    async def unsubscribe(self, sub: Subscriber) -> None:
        async with self._lock:
            self._subscribers.discard(sub)

    def _deliver(self, sub: Subscriber, event: dict[str, Any]) -> None:
        try:
            sub.queue.put_nowait(event)
        except asyncio.QueueFull:
            # 느린 소비자는 이벤트를 드롭(연결 자체는 유지). 필요 시 로깅.
            pass

    async def publish_to_user(self, user_id: int, event: dict[str, Any]) -> None:
        async with self._lock:
            targets = [s for s in self._subscribers if s.user_id == user_id]
        for sub in targets:
            self._deliver(sub, event)

    async def publish_to_group(self, group_id: int, event: dict[str, Any]) -> None:
        async with self._lock:
            targets = [s for s in self._subscribers if s.group_id == group_id]
        for sub in targets:
            self._deliver(sub, event)

    async def publish_to_group_boss(self, group_id: int, event: dict[str, Any]) -> None:
        async with self._lock:
            targets = [
                s for s in self._subscribers if s.group_id == group_id and s.role == "boss"
            ]
        for sub in targets:
            self._deliver(sub, event)

    async def publish_global(self, event: dict[str, Any]) -> None:
        async with self._lock:
            targets = list(self._subscribers)
        for sub in targets:
            self._deliver(sub, event)


# 앱 전역 단일 인스턴스
bus = EventBus()
