"""FastAPI 앱 엔트리포인트."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api import demo, stream
from app.core.config import settings
from app.core.database import engine

app = FastAPI(title="쫄병코인 API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict:
    """서버 + DB 연결 상태 확인."""
    db_ok = False
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_ok = True
    except Exception:
        db_ok = False
    return {"status": "ok", "db": db_ok}


# 라우터 등록
app.include_router(stream.router, prefix="/api", tags=["stream"])
app.include_router(demo.router, prefix="/api/demo", tags=["demo"])
