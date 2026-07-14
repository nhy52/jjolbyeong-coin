"""PoC 데모용 라우터.

정식 인증/가입 플로우 구현 전, SSE 실시간 코인 반영을 눈으로 확인하기 위한 임시 엔드포인트.
- POST /demo/seed  : 데모 그룹 + 대장 + 쫄병 + 지갑 생성(이미 있으면 재사용)
- POST /demo/grant : 대장이 쫄병에게 코인 지급 → 쫄병에게 SSE 통지

⚠️ 추후 정식 관리자 API(JWT 인증)로 대체 예정.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Group, MinionProfile, User, UserRole, UserStatus, Wallet
from app.services import coin

router = APIRouter()

DEMO_INVITE_CODE = "DEMO01"


class SeedResult(BaseModel):
    group_id: int
    boss_id: int
    minion_id: int
    minion_balance: int


class GrantRequest(BaseModel):
    minion_id: int
    amount: int
    reason: str | None = None


class GrantResult(BaseModel):
    minion_id: int
    balance: int
    delta: int


@router.post("/seed", response_model=SeedResult)
def seed(db: Session = Depends(get_db)) -> SeedResult:
    group = db.scalar(select(Group).where(Group.invite_code == DEMO_INVITE_CODE))
    if group is None:
        group = Group(name="데모 그룹", invite_code=DEMO_INVITE_CODE)
        db.add(group)
        db.flush()

    boss = db.scalar(select(User).where(User.email == "boss@demo.local"))
    if boss is None:
        boss = User(
            role=UserRole.boss,
            email="boss@demo.local",
            username="데모대장",
            password_hash="!demo!",  # 데모 전용, 로그인 불가
            group_id=group.id,
            status=UserStatus.active,
        )
        db.add(boss)
        db.flush()
        group.boss_user_id = boss.id

    minion = db.scalar(select(User).where(User.email == "minion@demo.local"))
    if minion is None:
        minion = User(
            role=UserRole.minion,
            email="minion@demo.local",
            username="데모쫄병",
            password_hash="!demo!",
            group_id=group.id,
            status=UserStatus.active,
        )
        db.add(minion)
        db.flush()
        db.add(MinionProfile(user_id=minion.id, name="데모쫄병", age=10, gender="M"))

    for u in (boss, minion):
        if db.scalar(select(Wallet).where(Wallet.user_id == u.id)) is None:
            db.add(Wallet(user_id=u.id, balance=0))

    db.commit()

    return SeedResult(
        group_id=group.id,
        boss_id=boss.id,
        minion_id=minion.id,
        minion_balance=coin.get_balance(db, minion.id),
    )


@router.post("/grant", response_model=GrantResult)
async def grant(req: GrantRequest, db: Session = Depends(get_db)) -> GrantResult:
    new_balance = await coin.grant_coins(
        db, req.minion_id, req.amount, reason=req.reason
    )
    return GrantResult(minion_id=req.minion_id, balance=new_balance, delta=req.amount)
