from fastapi import APIRouter
from sqlalchemy import text

from .. import db
from ..deps import get_current_user, CurrentUser
from fastapi import Depends

router = APIRouter(prefix="/api", tags=["meta"])


@router.get("/health")
def health():
    db_ok = False
    if db.engine is not None:
        try:
            with db.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            db_ok = True
        except Exception:
            db_ok = False
    return {"status": "ok", "db": "connected" if db_ok else "unconfigured"}


@router.get("/me")
def me(user: CurrentUser = Depends(get_current_user)):
    """1단계: 헤더 에코. 2단계(SSO): 세션에서 채워진 프로필 반환."""
    return {"name": user.name, "dept": user.dept, "role": user.role, "can_write": user.can_write}
