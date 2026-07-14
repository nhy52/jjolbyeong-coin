"""FastAPI 인증 의존성.

Authorization: Bearer <access_token> 헤더에서 토큰을 읽어 현재 사용자를 로드한다.
role/status 기반 접근 제어 의존성도 제공한다.
"""

from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_token
from app.models import User, UserRole, UserStatus

bearer_scheme = HTTPBearer(auto_error=True)

_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="인증이 필요합니다.",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(creds.credentials)
    except JWTError:
        raise _CREDENTIALS_EXC
    if payload.get("typ") != "access":
        raise _CREDENTIALS_EXC
    user_id = payload.get("sub")
    if user_id is None:
        raise _CREDENTIALS_EXC
    user = db.get(User, int(user_id))
    if user is None:
        raise _CREDENTIALS_EXC
    return user


def require_boss(user: User = Depends(get_current_user)) -> User:
    if user.role != UserRole.boss:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="대장 권한이 필요합니다.")
    return user


def require_active(user: User = Depends(get_current_user)) -> User:
    if user.status != UserStatus.active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="승인 대기 중이거나 비활성 계정입니다.",
        )
    return user
