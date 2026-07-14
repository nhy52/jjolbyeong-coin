"""인증/가입 도메인 로직.

- 대장 가입: 그룹 생성 + 초대 코드 발급 + 대장 계정(active) + 지갑
- 쫄병 가입: 초대 코드로 그룹 확인 + 쫄병 계정(pending) + 프로필 + 지갑
- 로그인 검증
"""

from __future__ import annotations

import secrets
import string

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models import (
    Group,
    MinionProfile,
    User,
    UserRole,
    UserStatus,
    Wallet,
)
from app.schemas import BossRegister, MinionRegister, MeOut
from app.services import coin

# 헷갈리기 쉬운 문자(0/O, 1/I) 제외
_INVITE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_INVITE_LEN = 6


def _email_taken(db: Session, email: str) -> bool:
    return db.scalar(select(User.id).where(User.email == email)) is not None


def _gen_invite_code(db: Session) -> str:
    for _ in range(20):
        code = "".join(secrets.choice(_INVITE_ALPHABET) for _ in range(_INVITE_LEN))
        if db.scalar(select(Group.id).where(Group.invite_code == code)) is None:
            return code
    raise RuntimeError("초대 코드 생성에 반복 실패했습니다.")


def register_boss(db: Session, data: BossRegister) -> User:
    if _email_taken(db, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 사용 중인 이메일입니다.")

    group = Group(
        name=data.group_name or f"{data.username}님의 그룹",
        invite_code=_gen_invite_code(db),
    )
    db.add(group)
    db.flush()

    boss = User(
        role=UserRole.boss,
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
        group_id=group.id,
        status=UserStatus.active,
    )
    db.add(boss)
    db.flush()

    group.boss_user_id = boss.id
    db.add(Wallet(user_id=boss.id, balance=0))
    db.commit()
    db.refresh(boss)
    return boss


def register_minion(db: Session, data: MinionRegister) -> User:
    group = db.scalar(
        select(Group).where(Group.invite_code == data.invite_code.strip().upper())
    )
    if group is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, "초대 코드에 해당하는 그룹을 찾을 수 없습니다."
        )
    if _email_taken(db, data.email):
        raise HTTPException(status.HTTP_409_CONFLICT, "이미 사용 중인 이메일입니다.")

    minion = User(
        role=UserRole.minion,
        email=data.email,
        username=data.username,
        password_hash=hash_password(data.password),
        group_id=group.id,
        status=UserStatus.pending,
    )
    db.add(minion)
    db.flush()

    db.add(
        MinionProfile(
            user_id=minion.id,
            name=data.name,
            phone=data.phone,
            address=data.address,
            gender=data.gender,
            age=data.age,
        )
    )
    db.add(Wallet(user_id=minion.id, balance=0))
    db.commit()
    db.refresh(minion)
    return minion


def authenticate(db: Session, email: str, password: str) -> User:
    user = db.scalar(select(User).where(User.email == email))
    if user is None or not verify_password(password, user.password_hash):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, "이메일 또는 비밀번호가 올바르지 않습니다."
        )
    return user


def build_me(db: Session, user: User) -> MeOut:
    """현재 사용자 정보 + 잔액 + 그룹 정보를 조합한다."""
    group = user.group
    invite_code = (
        group.invite_code if (user.role == UserRole.boss and group is not None) else None
    )
    return MeOut(
        id=user.id,
        role=user.role,
        username=user.username,
        email=user.email,
        status=user.status,
        group_id=user.group_id,
        group_name=group.name if group else None,
        invite_code=invite_code,
        balance=coin.get_balance(db, user.id),
    )
