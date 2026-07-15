"""ORM 모델 정의 (기획서 11장 데이터 모델 기준).

Alembic autogenerate가 모든 테이블을 인식하도록 이 모듈에서 모든 모델을 정의/노출한다.
"""

from __future__ import annotations

import enum
from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


# ----- Enums -----
class UserRole(str, enum.Enum):
    boss = "boss"
    minion = "minion"


class UserStatus(str, enum.Enum):
    pending = "pending"
    active = "active"
    suspended = "suspended"
    left = "left"


class CoinTxType(str, enum.Enum):
    GRANT = "GRANT"
    DEDUCT = "DEDUCT"
    PURCHASE = "PURCHASE"
    INVEST_BUY = "INVEST_BUY"
    INVEST_SELL = "INVEST_SELL"


class ProductStatus(str, enum.Enum):
    on_sale = "on_sale"
    sold_out = "sold_out"
    hidden = "hidden"


class OrderStatus(str, enum.Enum):
    purchased = "purchased"
    fulfilled = "fulfilled"
    canceled = "canceled"


class ProductRequestStatus(str, enum.Enum):
    pending = "pending"
    approved = "approved"
    rejected = "rejected"


class BittoSide(str, enum.Enum):
    buy = "buy"
    sell = "sell"


# 공용 컬럼 헬퍼
def _pk() -> Mapped[int]:
    return mapped_column(BigInteger, primary_key=True, autoincrement=True)


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)


# ----- Tables -----
class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = _pk()
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    invite_code: Mapped[str] = mapped_column(String(12), unique=True, index=True, nullable=False)
    boss_user_id: Mapped[int | None] = mapped_column(
        BigInteger,
        ForeignKey(
            "users.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_groups_boss_user_id",
        ),
        nullable=True,
    )
    created_at: Mapped[datetime] = _created_at()

    members: Mapped[list[User]] = relationship(
        back_populates="group", foreign_keys="User.group_id"
    )


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = _pk()
    role: Mapped[UserRole] = mapped_column(
        Enum(UserRole, native_enum=False, length=20), nullable=False
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    username: Mapped[str] = mapped_column(String(50), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    group_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("groups.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, native_enum=False, length=20),
        default=UserStatus.pending,
        nullable=False,
    )
    created_at: Mapped[datetime] = _created_at()

    group: Mapped[Group | None] = relationship(
        back_populates="members", foreign_keys=[group_id]
    )
    profile: Mapped[MinionProfile | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )
    wallet: Mapped[Wallet | None] = relationship(
        back_populates="user", uselist=False, cascade="all, delete-orphan"
    )


class MinionProfile(Base):
    __tablename__ = "minion_profiles"

    id: Mapped[int] = _pk()
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30))
    address: Mapped[str | None] = mapped_column(String(255))
    gender: Mapped[str | None] = mapped_column(String(10))
    age: Mapped[int | None] = mapped_column(Integer)

    user: Mapped[User] = relationship(back_populates="profile")


class Wallet(Base):
    __tablename__ = "wallets"

    id: Mapped[int] = _pk()
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    balance: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)

    user: Mapped[User] = relationship(back_populates="wallet")


class CoinTransaction(Base):
    __tablename__ = "coin_transactions"

    id: Mapped[int] = _pk()
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    type: Mapped[CoinTxType] = mapped_column(
        Enum(CoinTxType, native_enum=False, length=20), nullable=False
    )
    amount: Mapped[int] = mapped_column(BigInteger, nullable=False)  # +지급 / -차감
    reason: Mapped[str | None] = mapped_column(String(255))
    ref_id: Mapped[int | None] = mapped_column(BigInteger)  # 주문/거래 참조
    created_at: Mapped[datetime] = _created_at()


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = _pk()
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    price_coin: Mapped[int] = mapped_column(BigInteger, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[ProductStatus] = mapped_column(
        Enum(ProductStatus, native_enum=False, length=20),
        default=ProductStatus.on_sale,
        nullable=False,
    )
    stock: Mapped[int | None] = mapped_column(Integer)
    created_at: Mapped[datetime] = _created_at()


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[int] = _pk()
    product_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="RESTRICT"), nullable=False
    )
    buyer_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    price_paid: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, native_enum=False, length=20),
        default=OrderStatus.purchased,
        nullable=False,
    )
    created_at: Mapped[datetime] = _created_at()
    fulfilled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class ProductRequest(Base):
    """쫄병이 대장에게 '마켓에 올려달라'고 신청한 상품.

    대장이 승인하면 이 신청 내용(이름·희망가격·설명·이미지)으로 Product를 자동 생성하고
    product_id에 연결한다. 거절 시 reject_reason에 사유(선택)를 남긴다.
    """

    __tablename__ = "product_requests"

    id: Mapped[int] = _pk()
    group_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("groups.id", ondelete="CASCADE"), index=True, nullable=False
    )
    requester_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    desired_price: Mapped[int] = mapped_column(BigInteger, nullable=False)  # 쫄병 희망가(코인)
    description: Mapped[str | None] = mapped_column(Text)  # 신청 사유/설명
    image_url: Mapped[str | None] = mapped_column(String(500))  # 참고 이미지
    reference_url: Mapped[str | None] = mapped_column(String(500))  # 참고 링크
    status: Mapped[ProductRequestStatus] = mapped_column(
        Enum(ProductRequestStatus, native_enum=False, length=20),
        default=ProductRequestStatus.pending,
        nullable=False,
    )
    reject_reason: Mapped[str | None] = mapped_column(String(255))
    product_id: Mapped[int | None] = mapped_column(
        BigInteger, ForeignKey("products.id", ondelete="SET NULL"), nullable=True
    )  # 승인 시 생성된 상품
    created_at: Mapped[datetime] = _created_at()
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class BittoPrice(Base):
    __tablename__ = "bitto_prices"

    id: Mapped[int] = _pk()
    price: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)  # 전역 공용 시세
    created_at: Mapped[datetime] = _created_at()


class BittoHolding(Base):
    __tablename__ = "bitto_holdings"

    id: Mapped[int] = _pk()
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), default=0, nullable=False)
    avg_buy_price: Mapped[float] = mapped_column(Numeric(18, 2), default=0, nullable=False)


class BittoTrade(Base):
    __tablename__ = "bitto_trades"

    id: Mapped[int] = _pk()
    user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    side: Mapped[BittoSide] = mapped_column(
        Enum(BittoSide, native_enum=False, length=10), nullable=False
    )
    quantity: Mapped[float] = mapped_column(Numeric(18, 4), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(18, 2), nullable=False)
    created_at: Mapped[datetime] = _created_at()


__all__ = [
    "Base",
    "UserRole",
    "UserStatus",
    "CoinTxType",
    "ProductStatus",
    "OrderStatus",
    "ProductRequestStatus",
    "BittoSide",
    "Group",
    "User",
    "MinionProfile",
    "Wallet",
    "CoinTransaction",
    "Product",
    "ProductRequest",
    "Order",
    "BittoPrice",
    "BittoHolding",
    "BittoTrade",
]
