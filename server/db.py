"""DB 엔진/세션. DATABASE_URL 미설정 시 엔진 None → API 만 503, 정적 서빙은 계속."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from fastapi import HTTPException

from . import config

Base = declarative_base()

engine = None
SessionLocal = None

if config.DATABASE_URL:
    engine = create_engine(config.DATABASE_URL, pool_pre_ping=True, future=True)
    SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


def init_db():
    """테이블 생성. 앱 시작 시 호출 — DB 없으면 조용히 건너뜀."""
    if engine is None:
        return
    from . import models  # noqa: F401  (모델 등록)
    Base.metadata.create_all(bind=engine)


def get_db():
    """요청 단위 세션 의존성. DB 미연결이면 503."""
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail="DB 미연결: DATABASE_URL 환경변수(Secrets Manager ARN) 설정 필요")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
