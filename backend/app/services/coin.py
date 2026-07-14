"""코인 지급/차감 서비스.

잔액 변경은 항상 원장(coin_transactions)에 기록하고 wallets.balance를 갱신한다.
변경 후 SSE로 해당 사용자에게 실시간 알림을 보낸다.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.events.bus import bus
from app.models import CoinTransaction, CoinTxType, Wallet


class InsufficientBalanceError(Exception):
    """잔액 부족."""


def get_balance(db: Session, user_id: int) -> int:
    wallet = db.scalar(select(Wallet).where(Wallet.user_id == user_id))
    return wallet.balance if wallet else 0


def apply_transaction(
    db: Session,
    user_id: int,
    tx_type: CoinTxType,
    amount: int,
    reason: str | None = None,
    ref_id: int | None = None,
) -> int:
    """코인 잔액을 변경하고 원장에 기록한다. 갱신된 잔액을 반환.

    amount는 부호 포함(+지급, -차감). 동시성 방지를 위해 지갑 행을 잠근다.
    """
    wallet = db.scalar(
        select(Wallet).where(Wallet.user_id == user_id).with_for_update()
    )
    if wallet is None:
        wallet = Wallet(user_id=user_id, balance=0)
        db.add(wallet)
        db.flush()

    new_balance = wallet.balance + amount
    if new_balance < 0:
        raise InsufficientBalanceError()

    wallet.balance = new_balance
    db.add(
        CoinTransaction(
            user_id=user_id,
            type=tx_type,
            amount=amount,
            reason=reason,
            ref_id=ref_id,
        )
    )
    db.commit()
    return new_balance


async def grant_coins(
    db: Session, user_id: int, amount: int, reason: str | None = None
) -> int:
    """대장이 쫄병에게 코인을 지급(양수)한다. 갱신 잔액을 SSE로 통지."""
    if amount <= 0:
        raise ValueError("지급 금액은 1 이상이어야 합니다.")

    new_balance = apply_transaction(
        db, user_id, CoinTxType.GRANT, amount, reason=reason
    )

    await bus.publish_to_user(
        user_id,
        {
            "type": "coin.updated",
            "balance": new_balance,
            "delta": amount,
            "reason": reason,
        },
    )
    return new_balance
