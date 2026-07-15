"""API 요청/응답 스키마 (Pydantic)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import (
    OrderStatus,
    ProductRequestStatus,
    ProductStatus,
    UserRole,
    UserStatus,
)


# ----- 인증 -----
class BossRegister(BaseModel):
    email: EmailStr
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    group_name: str | None = Field(default=None, max_length=100)


class MinionRegister(BaseModel):
    email: EmailStr
    username: str = Field(min_length=1, max_length=50)
    password: str = Field(min_length=6, max_length=128)
    invite_code: str = Field(min_length=4, max_length=12)
    name: str = Field(min_length=1, max_length=50)
    phone: str | None = Field(default=None, max_length=30)
    address: str | None = Field(default=None, max_length=255)
    gender: str | None = Field(default=None, max_length=10)
    age: int | None = Field(default=None, ge=0, le=150)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MeOut(BaseModel):
    id: int
    role: UserRole
    username: str
    email: EmailStr
    status: UserStatus
    group_id: int | None = None
    group_name: str | None = None
    invite_code: str | None = None  # 대장에게만 제공
    balance: int = 0


class AuthResult(BaseModel):
    tokens: TokenPair
    user: MeOut


# ----- 대장 관리자 -----
class MinionSummary(BaseModel):
    id: int
    username: str
    name: str | None = None
    status: UserStatus
    balance: int
    created_at: datetime


class GrantRequest(BaseModel):
    amount: int = Field(gt=0)
    reason: str | None = Field(default=None, max_length=255)


class GrantResult(BaseModel):
    minion_id: int
    balance: int
    delta: int


class GroupSummary(BaseModel):
    group_id: int
    group_name: str
    invite_code: str
    total_minions: int
    active_minions: int
    pending_minions: int


# ----- 대장마켓: 상품 -----
class ProductCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price_coin: int = Field(gt=0)
    description: str | None = Field(default=None, max_length=2000)
    image_url: str | None = Field(default=None, max_length=500)
    stock: int | None = Field(default=None, ge=0)  # None = 무제한


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    price_coin: int | None = Field(default=None, gt=0)
    description: str | None = Field(default=None, max_length=2000)
    image_url: str | None = Field(default=None, max_length=500)
    stock: int | None = Field(default=None, ge=0)
    status: ProductStatus | None = None


class ProductOut(BaseModel):
    id: int
    name: str
    price_coin: int
    description: str | None = None
    image_url: str | None = None
    status: ProductStatus
    stock: int | None = None
    created_at: datetime


class ImageUploadResult(BaseModel):
    image_url: str


# ----- 대장마켓: 주문/구매 -----
class PurchaseResult(BaseModel):
    order_id: int
    product_id: int
    price_paid: int
    balance: int  # 구매 후 잔액


class OrderOut(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_image_url: str | None = None
    buyer_user_id: int
    buyer_name: str  # 프로필명 우선, 없으면 username
    price_paid: int
    status: OrderStatus
    created_at: datetime
    fulfilled_at: datetime | None = None


# ----- 대장마켓: 상품 신청(쫄병 → 대장) -----
class ProductRequestCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    desired_price: int = Field(gt=0)  # 희망 가격(코인)
    description: str | None = Field(default=None, max_length=2000)  # 신청 사유/설명
    image_url: str | None = Field(default=None, max_length=500)  # 참고 이미지
    reference_url: str | None = Field(default=None, max_length=500)  # 참고 링크


class ProductRequestReject(BaseModel):
    reason: str | None = Field(default=None, max_length=255)


class ProductRequestOut(BaseModel):
    id: int
    name: str
    desired_price: int
    description: str | None = None
    image_url: str | None = None
    reference_url: str | None = None
    status: ProductRequestStatus
    reject_reason: str | None = None
    product_id: int | None = None  # 승인 시 생성된 상품
    requester_user_id: int
    requester_name: str  # 프로필명 우선, 없으면 username
    created_at: datetime
    decided_at: datetime | None = None
