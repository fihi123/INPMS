from fastapi import APIRouter, Depends, HTTPException, Body, Query
from sqlalchemy.orm import Session
from typing import Optional

from ..db import get_db
from ..models import Request
from ..deps import get_current_user, CurrentUser
from .. import crud

router = APIRouter(prefix="/api/requests", tags=["requests"])


def _require_write(user: CurrentUser):
    if not user.can_write:
        raise HTTPException(status_code=403, detail="참조자(viewer)는 쓰기 권한이 없습니다.")


@router.get("")
def list_requests(
    db: Session = Depends(get_db),
    status: Optional[str] = None,
    urgency: Optional[str] = None,
    q: Optional[str] = Query(default=None, description="제품명/고객사/문서번호 부분일치"),
):
    """목록 — 첨부 blob 제외한 경량 payload 반환."""
    query = db.query(Request)
    if status:
        query = query.filter(Request.status == status)
    if urgency:
        query = query.filter(Request.urgency == urgency)
    if q:
        like = f"%{q}%"
        query = query.filter(
            (Request.product.ilike(like)) | (Request.client.ilike(like)) | (Request.docno.ilike(like))
        )
    rows = query.order_by(Request.created_at.desc()).all()
    return [crud.strip_attachment_blobs(r.payload or {}) for r in rows]


@router.get("/{req_id}")
def get_request(req_id: str, db: Session = Depends(get_db)):
    """상세 — 첨부 포함 전체 payload."""
    r = db.get(Request, req_id)
    if not r:
        raise HTTPException(status_code=404, detail="요청서를 찾을 수 없습니다.")
    return r.payload or {}


@router.post("", status_code=201)
def create_request(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_write(user)
    rid = payload.get("id")
    if not rid or not isinstance(rid, str):
        raise HTTPException(status_code=400, detail="id 누락")
    if db.get(Request, rid):
        raise HTTPException(status_code=409, detail="이미 존재하는 id")
    row = Request(
        id=rid,
        payload=payload,
        created_by_name=user.name,
        created_by_dept=user.dept,
        created_by_role=user.role,
        **crud.request_columns_from_payload(payload),
    )
    db.add(row)
    db.commit()
    return payload


@router.put("/{req_id}")
def update_request(
    req_id: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_write(user)
    row = db.get(Request, req_id)
    if not row:
        raise HTTPException(status_code=404, detail="요청서를 찾을 수 없습니다.")
    payload["id"] = req_id
    row.payload = payload
    for k, v in crud.request_columns_from_payload(payload).items():
        setattr(row, k, v)
    db.commit()
    return payload


@router.delete("/{req_id}", status_code=204)
def delete_request(
    req_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_write(user)
    row = db.get(Request, req_id)
    if row:
        db.delete(row)
        db.commit()
    return None
