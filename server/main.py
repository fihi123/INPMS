"""FastAPI 진입점.

- /api/*  : REST API (DB 필요)
- /       : 정적 프론트엔드(index.html, cosmax.png) — DB 없어도 동작
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from . import config, db
from .routers import health, requests, newproducts, migrate

app = FastAPI(title="INPMS API", version="1.0.0")

if config.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.CORS_ORIGINS,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.on_event("startup")
def _startup():
    db.init_db()  # DB 있으면 테이블 생성, 없으면 조용히 건너뜀


# API 라우터 (정적 마운트보다 먼저 등록)
app.include_router(health.router)
app.include_router(requests.router)
app.include_router(newproducts.router)
app.include_router(migrate.router)

# 정적 프론트엔드 — 루트 마운트(가장 마지막). html=True 로 index.html 자동 서빙.
app.mount("/", StaticFiles(directory=str(config.REPO_ROOT), html=True), name="static")
