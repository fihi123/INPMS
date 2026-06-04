# INPMS 백엔드 (FastAPI)

전체 설계는 저장소 루트 [`DESIGN.md`](../DESIGN.md) 참고.

## 로컬 실행 (SQLite)

```bash
cd /home/baek/INPMS
python3 -m venv .venv && source .venv/bin/activate
pip install -r server/requirements.txt
export DATABASE_URL="sqlite+pysqlite:///./dev.db"
uvicorn server.main:app --reload --port 8080
```

- 프론트엔드: http://localhost:8080/
- API 문서: http://localhost:8080/docs
- 헬스체크: http://localhost:8080/api/health

`DATABASE_URL` 을 비우면 정적 프론트엔드는 뜨고 `/api/*` 만 503 (선배포 검증용).

## 운영 배포 (App Runner)

1. I&S 에 사내 RDS(Postgres) 신청 → 자격증명 Secrets Manager ARN 수령.
2. 루트 `apprunner.yaml` 의 `run.secrets` 주석을 해제하고 ARN 입력.
3. push → 자동 배포. 시작 시 테이블 자동 생성(`init_db`).

## 데이터 이관

기존 앱 [백업] JSON 을 적재:

```bash
curl -X POST https://<도메인>/api/import \
  -H "Content-Type: application/json" \
  --data-binary @INPMS_시생산백업_xxxx.json
```

## 구조

```
server/
  main.py        FastAPI 앱, 정적 서빙 + 라우터 등록
  config.py      환경설정 (DATABASE_URL 등)
  db.py          엔진/세션, init_db, get_db 의존성
  models.py      Request / NewProduct (승격 컬럼 + JSONB payload)
  crud.py        payload <-> 컬럼 변환, 첨부 blob 스트립
  deps.py        현재 사용자 (1단계 헤더 / 2단계 SSO)
  routers/       health, requests, newproducts, migrate(import/export)
```
