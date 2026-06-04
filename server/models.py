"""ORM 모델. 하이브리드 매핑: 조회용 승격 컬럼 + 전체 레코드 JSONB payload."""
from sqlalchemy import Column, String, Boolean, DateTime, JSON, func
from sqlalchemy.dialects.postgresql import JSONB

from .db import Base

# Postgres 에서는 JSONB, sqlite(로컬개발) 에서는 JSON 으로 자동 매핑
PayloadType = JSON().with_variant(JSONB(), "postgresql")


class Request(Base):
    __tablename__ = "requests"

    id = Column(String, primary_key=True)
    # ---- 조회/필터/정렬용 승격 컬럼 (payload 에서 파생) ----
    docno = Column(String, index=True)
    status = Column(String, index=True)
    urgency = Column(String, index=True)
    risk = Column(String, index=True)
    scope = Column(String)
    reqdate = Column(String, index=True)
    client = Column(String, index=True)
    brand = Column(String)
    product = Column(String, index=True)
    fgcode = Column(String, index=True)
    pilotstatus = Column(String, index=True)
    pilotdate = Column(String)
    pdcheck = Column(String)
    richeck = Column(String)
    new_product_id = Column(String, index=True)
    # ---- 작성자 (1단계: 헤더, 2단계: SSO) ----
    created_by_name = Column(String)
    created_by_dept = Column(String)
    created_by_role = Column(String)
    # ---- 전체 레코드 (체크플래그/진행로그/서명/첨부 포함) ----
    payload = Column(PayloadType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class NewProduct(Base):
    __tablename__ = "new_products"

    id = Column(String, primary_key=True)
    week_key = Column(String, index=True)
    product_name = Column(String, index=True)
    brand = Column(String)
    customer = Column(String, index=True)
    category = Column(String, index=True)
    launch_date = Column(String)
    excluded = Column(Boolean, default=False, index=True)
    linked_request_id = Column(String, index=True)
    payload = Column(PayloadType, nullable=False, default=dict)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
