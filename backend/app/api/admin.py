"""대장(관리자) 전용 라우터.

모든 엔드포인트는 require_boss로 보호되며, 대장 자신의 그룹 범위에서만 동작한다.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_boss
from app.events.bus import bus
from app.models import MinionProfile, User, UserRole, UserStatus
from app.schemas import GrantRequest, GrantResult, GroupSummary, MinionSummary
from app.services import coin

router = APIRouter()


def _load_group_minion(db: Session, boss: User, minion_id: int) -> User:
    minion = db.get(User, minion_id)
    if (
        minion is None
        or minion.role != UserRole.minion
        or minion.group_id != boss.group_id
    ):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "그룹에 해당 쫄병이 없습니다.")
    return minion


@router.get("/summary", response_model=GroupSummary)
def summary(boss: User = Depends(require_boss), db: Session = Depends(get_db)) -> GroupSummary:
    group = boss.group
    if group is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "그룹을 찾을 수 없습니다.")

    def _count(status_filter: UserStatus | None) -> int:
        stmt = select(func.count(User.id)).where(
            User.group_id == group.id, User.role == UserRole.minion
        )
        if status_filter is not None:
            stmt = stmt.where(User.status == status_filter)
        return db.scalar(stmt) or 0

    return GroupSummary(
        group_id=group.id,
        group_name=group.name,
        invite_code=group.invite_code,
        total_minions=_count(None),
        active_minions=_count(UserStatus.active),
        pending_minions=_count(UserStatus.pending),
    )


@router.get("/minions", response_model=list[MinionSummary])
def list_minions(
    boss: User = Depends(require_boss), db: Session = Depends(get_db)
) -> list[MinionSummary]:
    rows = db.execute(
        select(User, MinionProfile.name)
        .join(MinionProfile, MinionProfile.user_id == User.id, isouter=True)
        .where(User.group_id == boss.group_id, User.role == UserRole.minion)
        .order_by(User.created_at.desc())
    ).all()

    return [
        MinionSummary(
            id=u.id,
            username=u.username,
            name=name,
            status=u.status,
            balance=coin.get_balance(db, u.id),
            created_at=u.created_at,
        )
        for (u, name) in rows
    ]


@router.post("/minions/{minion_id}/approve", response_model=MinionSummary)
async def approve_minion(
    minion_id: int, boss: User = Depends(require_boss), db: Session = Depends(get_db)
) -> MinionSummary:
    minion = _load_group_minion(db, boss, minion_id)
    if minion.status == UserStatus.pending:
        minion.status = UserStatus.active
        db.commit()
        db.refresh(minion)
        await bus.publish_to_user(
            minion.id, {"type": "minion.approved", "status": "active"}
        )
    return MinionSummary(
        id=minion.id,
        username=minion.username,
        name=minion.profile.name if minion.profile else None,
        status=minion.status,
        balance=coin.get_balance(db, minion.id),
        created_at=minion.created_at,
    )


@router.post("/minions/{minion_id}/reject")
async def reject_minion(
    minion_id: int, boss: User = Depends(require_boss), db: Session = Depends(get_db)
) -> dict:
    minion = _load_group_minion(db, boss, minion_id)
    minion.status = UserStatus.left
    db.commit()
    await bus.publish_to_user(minion.id, {"type": "minion.rejected", "status": "left"})
    return {"minion_id": minion.id, "status": "left"}


@router.post("/minions/{minion_id}/coins", response_model=GrantResult)
async def grant_coins(
    minion_id: int,
    req: GrantRequest,
    boss: User = Depends(require_boss),
    db: Session = Depends(get_db),
) -> GrantResult:
    minion = _load_group_minion(db, boss, minion_id)
    if minion.status != UserStatus.active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "승인된 쫄병에게만 지급할 수 있습니다.")
    new_balance = await coin.grant_coins(db, minion.id, req.amount, reason=req.reason)
    return GrantResult(minion_id=minion.id, balance=new_balance, delta=req.amount)
