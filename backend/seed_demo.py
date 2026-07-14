"""로그인 가능한 데모 계정을 생성/갱신하는 시드 스크립트.

README에 공개된 데모 대장/쫄병 계정을 누구나 바로 로그인해 볼 수 있도록,
실제 bcrypt 비밀번호로 계정을 만든다. 여러 번 실행해도 안전(idempotent)하며,
실행할 때마다 비밀번호를 문서화된 값으로 재설정해 항상 로그인되도록 보장한다.

실행:
    cd backend
    ./.venv/Scripts/python.exe seed_demo.py
"""

from __future__ import annotations

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models import (
    CoinTransaction,
    CoinTxType,
    Group,
    MinionProfile,
    User,
    UserRole,
    UserStatus,
    Wallet,
)

# ── 문서화된 데모 계정 정보 (README와 반드시 일치) ──
INVITE_CODE = "DEMO24"
GROUP_NAME = "데모 그룹"

BOSS_EMAIL = "boss@jjolcoin.app"
BOSS_PASSWORD = "demo1234"
BOSS_NAME = "데모대장"

MINION_EMAIL = "minion@jjolcoin.app"
MINION_PASSWORD = "demo1234"
MINION_NAME = "데모쫄병"
MINION_START_BALANCE = 480


def _ensure_wallet(db, user_id: int, balance: int) -> None:
    wallet = db.scalar(select(Wallet).where(Wallet.user_id == user_id))
    if wallet is None:
        db.add(Wallet(user_id=user_id, balance=balance))
    else:
        wallet.balance = balance


def main() -> None:
    db = SessionLocal()
    try:
        # 그룹
        group = db.scalar(select(Group).where(Group.invite_code == INVITE_CODE))
        if group is None:
            group = Group(name=GROUP_NAME, invite_code=INVITE_CODE)
            db.add(group)
            db.flush()

        # 대장
        boss = db.scalar(select(User).where(User.email == BOSS_EMAIL))
        if boss is None:
            boss = User(
                role=UserRole.boss,
                email=BOSS_EMAIL,
                username=BOSS_NAME,
                password_hash=hash_password(BOSS_PASSWORD),
                group_id=group.id,
                status=UserStatus.active,
            )
            db.add(boss)
            db.flush()
        else:
            boss.password_hash = hash_password(BOSS_PASSWORD)
            boss.status = UserStatus.active
            boss.group_id = group.id
        group.boss_user_id = boss.id
        _ensure_wallet(db, boss.id, 0)

        # 쫄병 (승인 완료 + 코인 보유)
        minion = db.scalar(select(User).where(User.email == MINION_EMAIL))
        if minion is None:
            minion = User(
                role=UserRole.minion,
                email=MINION_EMAIL,
                username=MINION_NAME,
                password_hash=hash_password(MINION_PASSWORD),
                group_id=group.id,
                status=UserStatus.active,
            )
            db.add(minion)
            db.flush()
            db.add(MinionProfile(user_id=minion.id, name=MINION_NAME, age=10, gender="M"))
        else:
            minion.password_hash = hash_password(MINION_PASSWORD)
            minion.status = UserStatus.active
            minion.group_id = group.id

        _ensure_wallet(db, minion.id, MINION_START_BALANCE)

        # 데모 느낌을 위한 지급 내역(원장) 1회만 시드
        has_ledger = db.scalar(
            select(CoinTransaction.id).where(CoinTransaction.user_id == minion.id)
        )
        if has_ledger is None:
            db.add_all(
                [
                    CoinTransaction(
                        user_id=minion.id, type=CoinTxType.GRANT, amount=300, reason="첫 출석"
                    ),
                    CoinTransaction(
                        user_id=minion.id, type=CoinTxType.GRANT, amount=180, reason="숙제 완료"
                    ),
                ]
            )

        db.commit()

        print("데모 계정 준비 완료 ✅")
        print(f"  그룹 초대코드 : {INVITE_CODE}")
        print(f"  대장 : {BOSS_EMAIL} / {BOSS_PASSWORD}")
        print(f"  쫄병 : {MINION_EMAIL} / {MINION_PASSWORD} (잔액 {MINION_START_BALANCE})")
    finally:
        db.close()


if __name__ == "__main__":
    main()
