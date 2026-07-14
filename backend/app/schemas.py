"""API 요청/응답 스키마 (Pydantic)."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models import UserRole, UserStatus


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
