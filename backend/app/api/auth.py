"""인증 라우터: 대장/쫄병 가입, 로그인, 토큰 갱신, 내 정보."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.models import User
from app.schemas import (
    AuthResult,
    BossRegister,
    LoginRequest,
    MeOut,
    MinionRegister,
    RefreshRequest,
    TokenPair,
)
from app.services import auth as auth_service

router = APIRouter()


def _issue(db: Session, user: User) -> AuthResult:
    tokens = TokenPair(
        access_token=create_access_token(user.id, user.role.value, user.group_id),
        refresh_token=create_refresh_token(user.id, user.role.value, user.group_id),
    )
    return AuthResult(tokens=tokens, user=auth_service.build_me(db, user))


@router.post("/boss/register", response_model=AuthResult, status_code=status.HTTP_201_CREATED)
def register_boss(data: BossRegister, db: Session = Depends(get_db)) -> AuthResult:
    user = auth_service.register_boss(db, data)
    return _issue(db, user)


@router.post("/minion/register", response_model=AuthResult, status_code=status.HTTP_201_CREATED)
def register_minion(data: MinionRegister, db: Session = Depends(get_db)) -> AuthResult:
    user = auth_service.register_minion(db, data)
    return _issue(db, user)


@router.post("/login", response_model=AuthResult)
def login(data: LoginRequest, db: Session = Depends(get_db)) -> AuthResult:
    user = auth_service.authenticate(db, data.email, data.password)
    return _issue(db, user)


@router.post("/refresh", response_model=TokenPair)
def refresh(data: RefreshRequest, db: Session = Depends(get_db)) -> TokenPair:
    try:
        payload = decode_token(data.refresh_token)
    except JWTError:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "유효하지 않은 갱신 토큰입니다.")
    if payload.get("typ") != "refresh":
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "갱신 토큰이 아닙니다.")
    user = db.get(User, int(payload["sub"]))
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "존재하지 않는 사용자입니다.")
    return TokenPair(
        access_token=create_access_token(user.id, user.role.value, user.group_id),
        refresh_token=create_refresh_token(user.id, user.role.value, user.group_id),
    )


@router.get("/me", response_model=MeOut)
def me(user: User = Depends(get_current_user), db: Session = Depends(get_db)) -> MeOut:
    return auth_service.build_me(db, user)
