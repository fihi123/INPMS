# INPMS — 사내 DB(PostgreSQL) 신청 요약

> COSMAX Incubation Portal(App Runner)에 배포할 **INPMS(시생산 통합 관리 시스템)** 의
> 백엔드 DB 신청용. 아래 내용을 ITSM 신청서 및 I&S 협의 시 그대로 사용.

## 1. 신청 경로 (ITSM)

```
ITSM(itsm.cosmax.com) > SR신청 > 인프라/보안
  > 인프라/보안 계정 신청(사용자) > Incubation Portal
  → [선택] 사내 AWS DB(postgres) 발급 항목 포함
```

문의/담당: **I&S팀 이기동 팀장, 손용혁 과장**

## 2. 신청 대상 시스템 개요

| 항목 | 내용 |
|---|---|
| 시스템명 | INPMS (시생산 통합 관리 시스템) |
| 배포 위치 | COSMAX Incubation Portal (AWS App Runner) |
| GitHub 레포 | fihi123/INPMS (회사 GitHub Enterprise 이관 예정) |
| 백엔드 | FastAPI (Python 3.11) |
| DB 엔진 | **PostgreSQL** (버전 무관, 14 이상 권장) |
| 용도 | 시생산 요청서·신제품 리스트·위험도 평가 데이터 다중 사용자 공유 저장 |

## 3. 요청 사항

### 3-1. RDS(PostgreSQL) 인스턴스
- **DB명**: `inpms` (또는 지정해주시는 명칭)
- **사양**: 최소 사양으로 충분 (예: db.t4g.micro ~ small).
  - 데이터: 텍스트 위주 레코드 + 첨부파일(BOM/MSDS/COA 등, 건당 ~2MB) 인라인 저장.
  - 초기 규모: 요청서 수백 건 + 신제품 리스트 수십~수백 건. 스토리지 20GB면 충분.
- **백업**: 자동 백업(스냅샷) 기본 정책 적용 요청.

### 3-2. 접속 정보를 Secrets Manager ARN으로 회신 요청
App Runner는 DB 자격증명을 **Secrets Manager ARN**으로 주입받습니다.
아래 형식 중 **하나**로 ARN을 만들어 회신 부탁드립니다.

**(권장) 단일 연결 문자열 시크릿** — 키 이름 `DATABASE_URL`, 값 형식:
```
postgresql+psycopg2://<user>:<password>@<host>:5432/inpms
```

**(대안) 항목 분리 시크릿** — 아래 키들로 저장해주셔도 백엔드가 조립합니다:
```
DB_HOST, DB_PORT(기본 5432), DB_NAME, DB_USER, DB_PASSWORD
```

회신받을 값: **`arn:aws:secretsmanager:ap-northeast-2:<account>:secret:inpms-db-xxxxxx`**

### 3-3. 네트워크
- RDS가 **private subnet**에 위치할 경우, App Runner 서비스의 발신 트래픽을 VPC로 설정하고
  **VPC 커넥터(`CM-App_Runner_VPC_Connector`)** 연결이 필요합니다 (포털 가이드 FAQ 참고).
- App Runner ↔ RDS 간 보안그룹 인바운드(5432) 허용 요청.

### 3-4. IAM (이미 포털 가이드에 명시된 역할)
- App Runner 서비스에 **`CM-Incubation-SecretManager-ReadOnly-Role`** 부여
  (Secrets Manager 읽기 → DB 자격증명 ARN 접근에 필요).

## 4. 회신받은 ARN 적용 방법 (신청자/개발 측 작업)

`apprunner.yaml`의 `run.secrets` 주석을 해제하고 회신받은 ARN 입력:

```yaml
run:
  command: uvicorn server.main:app --host 0.0.0.0 --port 8080
  network:
    port: 8080
  secrets:
    - name: DATABASE_URL
      value-from: "arn:aws:secretsmanager:ap-northeast-2:<account>:secret:inpms-db-xxxxxx"
```

push → 자동 재배포. 앱 시작 시 테이블 자동 생성(`init_db`).
연결 확인: `https://<서비스도메인>/api/health` → `{"db":"connected"}`.

> 참고: DB 미연결 상태로 먼저 배포해도 정적 화면은 동작하며(`/api/*`만 503),
> ARN 연결 후 재배포하면 다중 사용자 공유 모드로 전환됩니다.

## 5. 데이터 이관 (배포 후)

기존 사용자 브라우저의 [백업] JSON을 1회 적재:
```
POST https://<서비스도메인>/api/import   (Content-Type: application/json, 본문 = 백업 JSON)
```

## 6. (후속, 별도 신청) SSO

사내 계정 SSO는 별도 건으로 신청:
```
ITSM > SR신청 > 공통 > 시스템 개발/변경 > 업무시스템 : O365/Teams
인증방식: OAuth/MSAL (서비스명, 담당자, 리디렉션 URI, API 사용권한 등 제출)
```
승인 후 받은 애플리케이션 ID / 테넌트 ID / Secret Key 도 Secrets Manager 저장 → ARN 회신 요청.
문의(Teams): I&S팀 손용혁 과장, 전슬기 대리.
