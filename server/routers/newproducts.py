from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import NewProduct
from ..deps import get_current_user, CurrentUser
from .. import crud

router = APIRouter(prefix="/api/newproducts", tags=["newproducts"])


def _require_write(user: CurrentUser):
    if not user.can_write:
        raise HTTPException(status_code=403, detail="참조자(viewer)는 쓰기 권한이 없습니다.")


@router.get("")
def list_newproducts(db: Session = Depends(get_db)):
    rows = db.query(NewProduct).order_by(NewProduct.created_at.desc()).all()
    return [r.payload or {} for r in rows]


@router.post("", status_code=201)
def create_newproduct(
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_write(user)
    npid = payload.get("id")
    if not npid or not isinstance(npid, str):
        raise HTTPException(status_code=400, detail="id 누락")
    if db.get(NewProduct, npid):
        raise HTTPException(status_code=409, detail="이미 존재하는 id")
    row = NewProduct(id=npid, payload=payload, **crud.newproduct_columns_from_payload(payload))
    db.add(row)
    db.commit()
    return payload


@router.put("/{np_id}")
def update_newproduct(
    np_id: str,
    payload: dict = Body(...),
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_write(user)
    row = db.get(NewProduct, np_id)
    if not row:
        raise HTTPException(status_code=404, detail="신제품을 찾을 수 없습니다.")
    payload["id"] = np_id
    row.payload = payload
    for k, v in crud.newproduct_columns_from_payload(payload).items():
        setattr(row, k, v)
    db.commit()
    return payload


@router.delete("/{np_id}", status_code=204)
def delete_newproduct(
    np_id: str,
    db: Session = Depends(get_db),
    user: CurrentUser = Depends(get_current_user),
):
    _require_write(user)
    row = db.get(NewProduct, np_id)
    if row:
        db.delete(row)
        db.commit()
    return None
