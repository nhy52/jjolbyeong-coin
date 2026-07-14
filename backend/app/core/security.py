"""인증 보안 유틸: 비밀번호 해싱 + JWT 발급/검증."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def _pw_bytes(plain: str) -> bytes:
    # bcrypt는 최대 72바이트만 사용한다. 초과분은 잘라서 넘긴다(표준 동작).
    return plain.encode("utf-8")[:72]


def hash_password(plain: str) -> str:
    return bcrypt.hashpw(_pw_bytes(plain), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(_pw_bytes(plain), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        # 데모 계정 등 bcrypt 형식이 아닌 해시는 로그인 불가 처리
        return False


def _create_token(
    *, user_id: int, role: str, group_id: int | None, token_type: str, expires: timedelta
) -> str:
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": str(user_id),
        "role": role,
        "gid": group_id,
        "typ": token_type,
        "iat": now,
        "exp": now + expires,
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_access_token(user_id: int, role: str, group_id: int | None) -> str:
    return _create_token(
        user_id=user_id,
        role=role,
        group_id=group_id,
        token_type="access",
        expires=timedelta(minutes=settings.JWT_ACCESS_TOKEN_EXPIRE_MINUTES),
    )


def create_refresh_token(user_id: int, role: str, group_id: int | None) -> str:
    return _create_token(
        user_id=user_id,
        role=role,
        group_id=group_id,
        token_type="refresh",
        expires=timedelta(days=settings.JWT_REFRESH_TOKEN_EXPIRE_DAYS),
    )


def decode_token(token: str) -> dict[str, Any]:
    """토큰을 검증하고 payload를 반환. 실패 시 JWTError."""
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM])


def decode_token_safe(token: str) -> dict[str, Any] | None:
    try:
        return decode_token(token)
    except JWTError:
        return None
