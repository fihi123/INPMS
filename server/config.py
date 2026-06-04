"""환경 설정. App Runner에서는 Secrets Manager ARN이 환경변수로 주입된다."""
import os
from pathlib import Path

# 저장소 루트 (server/ 의 부모) — index.html, cosmax.png 정적 서빙용
REPO_ROOT = Path(__file__).resolve().parent.parent

# DB 연결 문자열. App Runner: run.secrets 로 Secrets Manager ARN 주입.
#   예) postgresql+psycopg2://user:pw@host:5432/dbname
# 미설정 시 엔진 None → 정적 페이지는 서빙, /api/* 만 503 (선배포 가능).
# 로컬 개발: DATABASE_URL=sqlite+pysqlite:///./dev.db
DATABASE_URL = os.environ.get("DATABASE_URL") or None

# 일부 Secret 은 host/user/pw 를 분리 저장한다. URL 이 없으면 조립 시도.
if not DATABASE_URL and os.environ.get("DB_HOST"):
    _u = os.environ.get("DB_USER", "")
    _p = os.environ.get("DB_PASSWORD", "")
    _h = os.environ.get("DB_HOST", "")
    _port = os.environ.get("DB_PORT", "5432")
    _name = os.environ.get("DB_NAME", "")
    DATABASE_URL = f"postgresql+psycopg2://{_u}:{_p}@{_h}:{_port}/{_name}"

# CORS 허용 오리진 (동일 출처 서빙이면 불필요하나 개발 편의상)
CORS_ORIGINS = [o for o in os.environ.get("CORS_ORIGINS", "").split(",") if o]
