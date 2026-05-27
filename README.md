# INPMS — Integrated New Product Management System

COSMAX 시생산 통합 관리 시스템. 단일 HTML 파일 + localStorage 기반으로 동작합니다.

## 테스트 URL

GitHub Pages: https://fihi123.github.io/INPMS/

## 구성

- `index.html` — 본체 (인라인 JS, 외부 의존성 없음)
- `cosmax.png` — 로고
- `note.md` — 개발 메모

## 사용

1. 위 URL 접속 → 로컬 프로필 선택 (작성자 / 검토자 / 참조자)
2. 데이터는 브라우저 localStorage에 저장됩니다. 서버에 올라가지 않습니다.
3. 백업/복원은 JSON export/import 기능 사용.

## 역할

| 역할 | 소속 |
|---|---|
| 작성자 | 마케팅 / 해외영업 / 연구소 |
| 검토자 | 공정개발팀 |
| 참조자 | 생산팀 / KS팩 |

향후 사내 SSO 연결 예정 (현재 스키마는 SSO 호환 설계).
