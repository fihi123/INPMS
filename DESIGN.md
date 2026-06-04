# INPMS DB + 백엔드 전환 설계

> 현재: 단일 `index.html` + localStorage (브라우저별 저장, 5MB 한계, 다중 사용자 공유 불가)
> 목표: COSMAX Incubation Portal(AWS App Runner)에 FastAPI + PostgreSQL 백엔드로 배포, 다중 사용자 공유

확정 방향 (2026-06-04):
- 백엔드: **FastAPI (Python 3.11)**
- 마이그레이션: **점진적 — 기존 프론트엔드 유지, 저장 계층(localStorage)만 API 호출로 교체**
- SSO: **2단계 — DB 먼저, Entra ID SSO는 ITSM 승인 후 추가**

---

## 1. 아키텍처

```
[브라우저] index.html (기존 UI 유지)
   │  fetch() — js/api-client.js (localStorage 함수 대체)
   ▼
[App Runner] FastAPI (server/)
   │  SQLAlchemy
   ▼
[RDS] PostgreSQL  ── DB 자격증명은 Secrets Manager ARN (I&S 제공)
```

- App Runner 단일 서비스가 **정적 프론트엔드(index.html, cosmax.png)** 와 **REST API(/api/*)** 를 동시 서빙.
- DB 미연결(ARN 미설정) 시에도 앱은 부팅 → 정적 페이지는 동작, `/api/*` 만 503. ARN 받기 전 선배포 가능.

## 2. 데이터 모델 → 관계형 매핑

기존 요청서 객체는 ~80개 필드 + 체크리스트 + 진행 로그 + 첨부 + 위험도로 구성. 전 필드를 컬럼으로 쪼개면 브리틀하고 점진 전환을 방해한다. → **하이브리드 매핑**:

### `requests`
| 컬럼 | 용도 |
|---|---|
| `id` (PK, text `R...`) | 기존 ID 그대로 |
| `docno, status, urgency, risk, scope, reqdate, client, brand, product, fgcode, pilotstatus, pilotdate, pdcheck, richeck, new_product_id` | **조회/필터/정렬용 승격 컬럼** (payload에서 파생) |
| `payload` (JSONB) | **전체 레코드** (체크 플래그 `chk_*`, 진행 로그 `updates[]`, 서명, 첨부 등 모두 포함) |
| `created_by_name/dept/role` | 작성자 (1단계: 헤더, 2단계: SSO) |
| `created_at, updated_at` | 타임스탬프 |

- 프론트엔드는 **payload를 그대로 주고받음** → 객체 형태 불변(점진 전환 핵심).
- 승격 컬럼은 write 시 payload에서 자동 추출. 서버측 필터링/인덱스에만 사용.

### `new_products`
| 컬럼 | 용도 |
|---|---|
| `id` (PK, text) | 기존 ID |
| `week_key, product_name, brand, customer, category, launch_date, excluded, linked_request_id` | 승격 컬럼 |
| `payload` (JSONB) | 전체 레코드 (3부서 위험도 `risk{rnd,process,quality}`, inputBy 등) |
| `created_at, updated_at` | |

### 첨부 파일 (1단계 결정)
- 현재 `doc_*` / `photo_*` 필드가 base64로 객체 안에 인라인 → **localStorage 5MB 한계의 주범**.
- **1단계: payload JSONB에 그대로 인라인 저장.** Postgres 행은 사실상 용량 제한이 없어 5MB 한계가 즉시 사라짐. 프론트엔드 변경 최소.
- **목록 API는 첨부 blob(`data`)을 제거한 경량 payload 반환**, 상세 API만 전체 반환 → 목록이 메가바이트 base64로 부풀지 않음.
- **2단계(최적화, 선택): `attachments` 테이블 또는 S3 분리.** S3는 별도 IAM 역할(현재 역할은 SecretManager 전용)이 필요하므로 I&S 협의 후 진행. 이때 payload에는 참조(id/name/size)만 남기고 blob은 `/api/attachments/{id}`로 지연 로드.

## 3. REST API

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/api/health` | 헬스체크 + DB 연결 상태 |
| GET | `/api/requests` | 목록(필터: status, urgency, q) — 첨부 blob 제외 |
| GET | `/api/requests/{id}` | 상세 — 전체 payload(첨부 포함) |
| POST | `/api/requests` | 생성 |
| PUT | `/api/requests/{id}` | 전체 갱신 |
| DELETE | `/api/requests/{id}` | 삭제 |
| GET | `/api/newproducts` | 목록 |
| POST/PUT/DELETE | `/api/newproducts[/{id}]` | CRUD |
| POST | `/api/import` | 백업 JSON 일괄 적재(기존 사용자 데이터 이관) |
| GET | `/api/export` | 전체 백업 JSON (기존 exportBackup 호환 형식) |
| GET | `/api/me` | 현재 사용자 프로필 (1단계: 헤더 에코, 2단계: SSO) |

- 자동 OpenAPI 문서: `/docs` (FastAPI 기본 제공).

## 4. 인증 (2단계)

- **1단계 (현재)**: 프론트엔드가 로컬 프로필을 `X-User-Name / X-User-Role / X-User-Dept` 헤더로 전달. 서버는 이를 신뢰하고 `created_by`에 기록(사내망 한정, 위변조 방지 없음). 기존 프로필 선택 UI 그대로 사용.
- **2단계 (SSO)**: ITSM(itsm.cosmax.com) > SR신청 > 공통 > 시스템 개발/변경 > O365/Teams 로 Entra ID(OAuth/MSAL) 신청. 승인 후 받은 App ID/Tenant ID/Secret을 Secrets Manager에 저장(ARN은 I&S). 백엔드에 인증 미들웨어 추가 → 세션에서 role/dept 도출, 위 헤더 대신 세션 사용. **DB·API 계약은 1단계와 동일**하므로 프론트엔드 영향 최소.
- 역할 매핑: 기존 `author/reviewer/viewer` ↔ SSO 그룹/속성. 쓰기 권한(생성·편집)은 서버에서 role 검증.

## 5. 프론트엔드 점진 전환

기존 동기식 in-memory 배열(`requests`, `newProducts`)을 **로컬 캐시**로 유지하고, 저장 함수만 비동기 API 호출로 교체.

교체 대상 함수 (index.html):
- `loadData()` / `loadNewProducts()` → 시작 시 `GET /api/requests`, `/api/newproducts`로 캐시 채움 (앱 부트를 async로)
- `saveData()` → 변경된 단건을 `POST/PUT /api/requests`로 동기화 (전체 배열 저장 대신 단건 sync)
- `saveNewProducts()` → 단건 `POST/PUT /api/newproducts`
- 삭제 경로 → `DELETE`
- 편집 폼 열 때 → `GET /api/requests/{id}`로 첨부 포함 전체 로드
- `loadProfile/saveProfile` → 1단계 유지(로컬), 2단계에 `/api/me`로 교체
- 백업/복원 → `/api/export`, `/api/import` 호출(기존 JSON 다운로드도 폴백 유지)

새 모듈 `js/api-client.js`가 위 매핑을 캡슐화 → index.html 변경 범위를 호출부로 한정.

> 이 단계(프론트 호출부 교체)는 본 커밋의 백엔드 스캐폴드 위에서 별도 작업으로 진행(리스크 격리). 백엔드/스키마/배포 설정이 먼저 안정화된 뒤 호출부를 바꾼다.

## 6. 데이터 이관

기존 사용자는 앱의 **[백업]** 기능으로 받은 JSON(`{data, newProducts}`)을 `POST /api/import`로 1회 업로드 → DB 적재. 멱등(같은 id 재업로드 시 upsert).

## 7. 배포 (App Runner)

- `apprunner.yaml`: runtime `python311`, build `pip install -r server/requirements.txt`, run `uvicorn server.main:app --host 0.0.0.0 --port 8080`.
- **DB**: I&S에 사내 AWS RDS(Postgres) 신청 → 자격증명 Secrets Manager ARN 회신 → apprunner.yaml `run.secrets`에 `DATABASE_URL`로 주입.
- IAM 역할: `CM-Incubation-SecretManager-ReadOnly-Role` (Secret 읽기).
- 네트워크: RDS가 private subnet이면 VPC 커넥터 연결 필요(가이드 FAQ).
- 도메인: `inpms.cosmaxhub.com` 등 커스텀 도메인(SSL 자동).

## 8. 단계별 실행 순서

1. **(완료)** 백엔드 스캐폴드 + apprunner.yaml — 정적 서빙 유지하며 API 준비.
2. I&S에 RDS(Postgres) 신청 → DATABASE_URL ARN 수령 → apprunner secrets 연결, 테이블 생성.
3. 프론트엔드 저장 계층을 `js/api-client.js`로 교체(점진).
4. 기존 데이터 `/api/import`로 이관.
5. SSO(Entra ID) ITSM 신청 → 미들웨어 추가(2단계).
6. 첨부 S3 분리(선택, 최적화).
