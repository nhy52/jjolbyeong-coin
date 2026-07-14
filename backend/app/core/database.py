from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    echo=False,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    """모든 ORM 모델의 베이스 클래스."""


def get_db() -> Generator[Session, None, None]:
    """FastAPI 의존성: 요청마다 DB 세션을 열고 종료 시 닫는다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
