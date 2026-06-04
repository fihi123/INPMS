"""백업 JSON 일괄 적재/내보내기 — 기존 localStorage 데이터 이관용.

기존 exportBackup() 형식과 호환:
  { app, version, schemaVersion, data: [...requests], newProducts: [...] }
"""
from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import Request, NewProduct
from ..deps import get_current_user, CurrentUser
from .. import crud

router = APIRouter(prefix="/api", tags=["migrate"])


@router.post("/import")
def import_backup(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    """멱등 upsert. 같은 id 재업로드 시 갱신."""
    reqs = payload.get("data") or []
    nps = payload.get("newProducts") or []
    n_req = n_np = 0

    for rec in reqs:
        if not isinstance(rec, dict) or not rec.get("id"):
            continue
        row = db.get(Request, rec["id"])
        cols = crud.request_columns_from_payload(rec)
        if row:
            row.payload = rec
            for k, v in cols.items():
                setattr(row, k, v)
        else:
            row = Request(
                id=rec["id"], payload=rec,
                created_by_name=user.name, created_by_dept=user.dept, created_by_role=user.role,
                **cols,
            )
            db.add(row)
        n_req += 1

    for rec in nps:
        if not isinstance(rec, dict) or not rec.get("id"):
            continue
        row = db.get(NewProduct, rec["id"])
        cols = crud.newproduct_columns_from_payload(rec)
        if row:
            row.payload = rec
            for k, v in cols.items():
                setattr(row, k, v)
        else:
            db.add(NewProduct(id=rec["id"], payload=rec, **cols))
        n_np += 1

    db.commit()
    return {"imported": {"requests": n_req, "newProducts": n_np}}


@router.get("/export")
def export_backup(db: Session = Depends(get_db)):
    """기존 백업 JSON 형식으로 전체 반환(첨부 포함)."""
    reqs = [r.payload or {} for r in db.query(Request).all()]
    nps = [n.payload or {} for n in db.query(NewProduct).all()]
    return {
        "app": "cosmax_pilot_requests",
        "version": 4,
        "schemaVersion": 2,
        "count": len(reqs),
        "newProductCount": len(nps),
        "data": reqs,
        "newProducts": nps,
    }
