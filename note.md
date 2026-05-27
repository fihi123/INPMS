# INPMS 프로젝트 노트

> COSMAX 시생산 통합 관리 시스템 (Integrated New Product Management System)
> 이 파일은 Claude Code / Gemini CLI 등 여러 AI 도구 간 맥락 공유용 메모입니다.

---

## 1. 프로젝트 개요

- **목적**: COSMAX 시생산 요청/검토/주차별 업데이트 워크플로우 관리
- **배경**: 동화약품 립크림 이슈 이후 프로세스 재정립
- **형태**: 단일 HTML 파일 + 인라인 JS + localStorage (외부 백엔드 없음)
- **백업 방식**: JSON 파일 export/import 로 수동 공유
- **위치**: `/home/baek/INPMS/Integrated New Product Management System.html`

---

## 2. 파일 구조

```
/home/baek/INPMS/
├── Integrated New Product Management System.html   # 본체 (단일 파일)
├── cosmax.png                                      # 로고
├── note.md                                         # 이 문서
└── .claude/                                        # Claude Code 설정
```

---

## 3. 화면 구성 (탭)

| 탭 | ID | 역할 |
|---|---|---|
| 📊 대시보드 | `tab-dashboard` | 통계 카드, 요약 |
| 📋 요청 품목 리스트 | `tab-list` | 시생산 요청 목록 + 필터 |
| 📅 주차별 업데이트 | `tab-weekly` | ISO 주차 기준 진행현황 |
| 🔄 프로세스 안내 | `tab-process` | 워크플로우 가이드 |

탭 전환: `switchTab(name, el)` → `renderCurrent()` 호출로 현재 탭만 다시 그림.

---

## 4. 핵심 JS 함수 (재사용 필수)

### 데이터 레이어
- `loadData()` — localStorage에서 데이터 로드
- `saveData()` — 저장. **불리언 반환값 반드시 체크** (용량 초과/실패 대비)
- `genId()` — `R{timestamp}{rand}` 형식 고유 ID
- `nextDocNo()` — 연도별 최대값+1 방식 문서번호

### 렌더
- `renderStats()` / `renderList()` / `renderWeekly()` / `renderUpdatesList()`
- `renderCurrent()` — 현재 탭만 갱신 (전체 리렌더 X)

### 보안/포매팅 헬퍼 (신규 코드에 반드시 재사용)
- `escapeHtml(s)` / `esc(s)` — HTML 이스케이프
- `dash(s)` — null/빈값 → `-`, 아니면 escape
- `safeId(s)` — `R\d+` 패턴만 허용
- `isCapaOk(v)` — CAPA 정상 여부
- `safePhotoSrc(s)` — 이미지 src 검증

### 상태/라벨 매핑
- `statusBadge` / `statusLabel` — pending / progress / done / issue
- `urgencyBadge` / `urgencyLabel` — normal / urgent / critical
- `scopeBadge` — 제조+충진/포장 / 제조만 / 충진·포장만
- `pilotStatusBadge` — 예정 / 진행중 / 완료 / 중단
- `deriveStatus(current, richeck, pdcheck)` — 파생 상태 계산

### 폼/첨부
- `openForm()` / `editItem(id)` / `saveForm()` / `deleteItem()`
- `saveUpdate()` / `editUpdate(idx)` / `removeUpdate(idx)` — 주차별 업데이트
- `handlePhotoUpload(e, kind)` / `renderPhotoPreview(kind)` / `removePhoto(kind)`
- `renderAttachments(r)`

---

## 5. 작업 시 주의사항 (feedback)

1. **XSS 방지**: 백업 JSON 복원 경로로 저장된 XSS가 가능함.
   → 모든 동적 렌더에 `escapeHtml`/`esc`/`dash` 필수.
2. **저장 실패 처리**: `saveData()` 리턴값 확인 후 사용자에게 실패 알림.
3. **탭 부분 렌더**: 전체 리렌더 대신 `renderCurrent()` 사용.
4. **ID/문서번호**: 직접 생성하지 말고 `genId()`, `nextDocNo()` 재사용.

---

## 6. 작업 로그 (수동 기록)

> AI 도구를 바꿀 때마다 여기에 한 줄씩 남겨두면 맥락 이어가기 편함.

- 2026-04-23 : note.md 초기 작성 (Claude Code)
- 2026-04-23 : Gemini CLI를 통한 코드 분석 및 개선안 섹션 추가
- 2026-04-23 : 섹션 8 우선순위 기반 재작성 (Claude Code)
- 2026-04-23 : P0/P1 구현 완료 (Claude Code)
  - `META_KEY`/`SCHEMA_VERSION`/`BACKUP_REMIND_DAYS` 상수 + `loadMeta`/`saveMeta` 도입 (별도 localStorage 키 `cosmax_pilot_meta_v1`)
  - `saveData()` 실패 시 quota 판별 + 구체적 복구 단계 안내
  - `sanitizeImportRecord()`/`sanitizeUpdate()` 필드 화이트리스트 검증 — import 시 허용된 필드만 통과, 타입 강제, 사진은 `safePhotoSrc`로 재검증, id는 정규식 실패 시 재생성
  - import 시 schemaVersion 비교 경고, 드롭된 레코드 수 안내
  - `exportBackup()` 파일명 `INPMS_시생산백업_YYYY-MM-DD_HHMM_N건.json` + `meta.lastExport` 기록
  - 대시보드 상단 백업 알림 배너 (backup 기록 없거나 7일 초과 시)
  - `saveForm()` 날짜 순서 검증 — 완료일<예정일, 예정일<요청일, 발매일<완료일 (confirm으로 강제 아님)
  - 리스트 탭 `↺ 초기화` 버튼 (`resetListFilters()`) — 검색+필터 3개 일괄 리셋
  - XSS 감사 결과: 기존 `esc`/`dash`/`safeId`/`safePhotoSrc` 헬퍼가 체계적으로 적용되어 있어 실제 취약점 없음 — 별도 수정 없이 완료
- 2026-04-23 : P2 + 역할별 개선 전체 구현 (Claude Code)
  - **A-1 삭제 Undo**: `deleteItem()` → 삭제 후 5초 스낵바, `되돌리기` 클릭 시 원위치 복구 (index 유지)
  - **A-2a 복제**: `duplicateItem(id)` — 기존 요청서를 템플릿으로 새 요청서 생성. 날짜/배치/물성 판정값/서명/메모/CAPA/라인은 비움. 리스트 📑 버튼 + 상세 모달 📑 복제 버튼.
  - **A-2b 클립보드 복사**: `copyRequestToClipboard(id)` — 주요 필드를 섹션 정렬 텍스트로 복사. `navigator.clipboard` → `execCommand` fallback. 상세 모달 📋 텍스트 복사 버튼.
  - 공용 스낵바 시스템 (`showSnackbar`/`hideSnackbar`/`handleSnackUndo`) — 향후 다른 Undo/알림에도 재사용 가능
  - **B-0 프로필 시스템** (SSO 호환): `cosmax_pilot_profile_v1` 키. `profile = {role, dept, name, email, org}` 구조. `ROLES`/`DEPTS_BY_ROLE` 상수 + `getProfile`/`saveProfile`/`hasProfile`/`isRole`/`isDept` 래퍼. 헤더 👤 버튼, 프로필 모달, 미설정 시 대시보드 배너. 향후 SSO 전환 시 `loadProfile` 교체만으로 동작.
  - **B-9 읽기전용 모드**: `.role-viewer .write-only { display:none }` + `openForm/editItem/duplicateItem/openQuickUpdate` 진입 가드. 헤더에 "읽기 전용" 배지.
  - **B-5 공정개발 검토 큐**: 대시보드 `#reviewer-queue` (reviewer-only 클래스). 내 검토 대기 / 긴급 대기 / 이번 주 시생산 예정 미완 3개 카드. 클릭 시 `jumpToReviewerQueue(kind)` → 리스트 탭 + `reviewerQueueFilter` 좁힘 + 우선순위 정렬 자동 전환.
  - **B-1 부서별 form 프리셋**: `openDefaultTabForProfile()` — 연구소=벌크, 공정개발=업데이트, 나머지=기본 탭으로 시작.
  - **B-2 해외영업 수출 정보**: 새 섹션 `#section-export`, `xp = {countries, cert[], translation, note}`. `readExportFromForm`/`writeExportToForm`/`updateExportSectionVisibility`. `sanitizeExport` 화이트리스트(`CERT_OK`). overseas 프로필이거나 `xp` 데이터 있을 때만 노출. 상세/클립보드/복제에 반영.
  - **B-3 섹션별 작성자/날짜**: `SECTION_FIELDS` 매핑 + `diffSection`/`stampSectionMeta`/`sanitizeSectionMeta`. saveForm에서 변경된 섹션만 `sectionMeta[key] = {editor, at}` 기록. 상세 모달에 "✍ 편집: 이름/부서 · 날짜" 표시. xp도 동일 처리.
  - **B-6 검토 우선순위 정렬**: 리스트 탭 `#sort-list` (요청일/우선순위/시생산예정일). `priorityScore(r)` — urgency(5/15/30) + days_waiting(0-30) + pilot_date_proximity(0-20) + pdPending(8) + issueBoost(10). done은 0점으로 하단.
  - **B-7 라인/CAPA 구조화**: `f-lineKey`(드롭다운 P1-A~P3-B/KSPACK/OTHER) + 자유 `f-line` 병행. `f-capaOk`(OK/NG) + 자유 수치 `f-capa`. `recordCapaOk(r)`로 명시값 우선, 자유 텍스트 휴리스틱 fallback.
  - **B-8 PD 의견 타임라인**: `renderPdTimeline(ups)` — stage에 '공정' 또는 author에 '공정개발' 포함한 updates만 필터한 별도 섹션 (파란 border-left).

---

## 7. AI 도구 간 전환 체크리스트

다른 도구(Gemini CLI 등)로 넘어갈 때:
- [ ] 현재 작업 중인 기능/탭 이름 기록
- [ ] 수정 중인 함수명과 라인 번호 기록
- [ ] 테스트해야 할 시나리오 메모
- [ ] 미결 이슈/결정 필요 사항 남기기

---

## 8. 개선안 (우선순위순)

이 도구의 특성 — **단일 HTML + localStorage + 수동 JSON 공유 + 내부 도구** — 을 고려하면, UI 화려함보다 **데이터 안정성**이 압도적으로 중요함. 우선순위는 이 기준으로 정렬됨.

### 🔴 P0 — 데이터 안정성 (반드시)

1. **백업 JSON import 시 스키마 검증**
   - 현재 섹션 5에 "백업 복원 경로로 저장된 XSS 가능"이라 명시돼 있지만, 대응책이 없음
   - 필드 화이트리스트 + 타입 체크로 오염된 JSON 차단
   - 이게 XSS 감사보다 먼저 — 오염 데이터는 렌더 전에 걸러야 함

2. **`saveData()` 실패 UX 완성**
   - 반환값 체크 규칙은 있지만, 5MB 초과 시 사용자가 **무엇을 해야 하는지** 안내 필요
   - quota exceeded → "사진 첨부를 줄이거나 오래된 항목을 백업 후 삭제하세요" 등

3. **innerHTML 사용 13곳 실감사**
   - 중점 감사: line 759(대시보드 긴급), 826(리스트), 882(주차별), 1132(업데이트 목록), 1381(모달 body)
   - template literal `${}` 안에 `esc()`/`escapeHtml()` 누락 확인

4. **`schemaVersion` 필드 도입**
   - 저장 데이터에 `schemaVersion: 1` 추가
   - 향후 구조 변경 시 기존 백업 JSON 마이그레이션 경로 확보
   - 지금 안 넣으면 나중에 고통받음

### 🟡 P1 — 실용적 개선 (효용 높음)

5. **백업 알림 (lastExport > 7일)**
   - `lastExport` 타임스탬프 저장
   - 대시보드 상단 배너로 "마지막 백업 N일 전" 경고
   - 이 도구 특성상 가장 효과 큰 UX 개선

6. **완료일 < 시작일 등 날짜 유효성 검증**
   - `saveForm()` 단계에서 경고
   - 기본기 수준

7. **필터 초기화 버튼**
   - 현재 검색 + 상태 + 긴급도 + 부서 4개 필드. 실제로 불편할 만함
   - 비용 싸고 효용 있음

8. **export 파일명 규칙**
   - `INPMS_YYYY-MM-DD_HHMM.json` 형식
   - 여러 백업 섞였을 때 최신 판별 가능

### 🟢 P2 — Nice to have

9. **삭제 Undo** — `deleteItem()` 즉시 삭제 → 되돌리기 스낵바 또는 휴지통
10. **복사 기능** — 사용자가 실제 요청했을 때만 (브라우저 드래그 복사로 커버되는지 먼저)

### ❌ 권장하지 않음 (비용 > 효용)

- **다크 모드** — 내부 도구에 CSS 변수/토글/저장 추가 비용 대비 효용 낮음
- **바 차트 시각화** — 5개 숫자에 차트 오버엔지니어링. 이미 26px 볼드로 충분히 명확
- **새 키보드 단축키** — line 2174에 이미 `keydown` 리스너 있음. 먼저 파악 후 판단
- **추가 사진 압축** — 이미 `toDataURL('image/jpeg', 0.7)` 압축 중 (line 1204). 개수 제한이 더 실용적

### 📝 보류 — 추가 조사 필요

- **다중 사용자 merge 전략** — "수동 JSON 공유"의 충돌 해결 정책이 명시돼 있지 않음. 실제 운영 시나리오 확인 후 방침 결정

---

## 8-A. 실사용 검증 체크리스트 (완료분)

브라우저에서 직접 확인해야 하는 시나리오. 코드상 문제없어 보여도 UX 실제 동작 확인용.

### P0/P1 (이전 작업)
- [ ] **import sanitize**: 일부러 `<script>alert(1)</script>` 삽입한 JSON / 이상한 `status` 값 / 잘못된 `id` 포함한 백업 import 시 **드롭 건수 알림**이 뜨고 XSS 실행 안 됨
- [ ] **quota 초과 메시지**: 사진 여러 장 주입해 5MB 초과 시 **구체적 복구 안내** 문구 (사진 줄이기, 오래된 항목 삭제 등) 노출
- [ ] **백업 배너**: DevTools 콘솔 `localStorage.removeItem('cosmax_pilot_meta_v1')` 후 새로고침 → 대시보드 상단 배너 표시. 또는 `meta.lastExport`를 8일 전 타임스탬프로 수정.
- [ ] **날짜 검증 confirm**: 완료일 < 예정일 / 예정일 < 요청일 / 발매일 < 완료일 중 하나 입력 후 저장 → confirm 경고 발생
- [ ] **필터 초기화**: 리스트 탭에서 검색·상태·긴급도·부서 4개 필드 채운 뒤 `↺ 초기화` 한 번에 리셋
- [ ] **schemaVersion 경고**: schemaVersion 필드 없거나 다른 값인 백업 JSON import 시 경고 메시지

### P2 (2026-04-23 신규)
- [ ] **삭제 Undo**: 요청서 편집 → 삭제 → 하단에 스낵바 표시 → "되돌리기" 클릭 시 리스트에 원위치 복구. 5초 후 스낵바 자동 사라지면 복구 불가.
- [ ] **복제**: 리스트 📑 버튼 또는 상세 모달 📑 복제 → 신규 요청서 form 열림. 문서번호 새로 생성, 요청일 오늘. 날짜·배치·서명·라인·CAPA·물성 판정값은 빈 칸.
- [ ] **복제 후 저장**: 복제로 만든 요청서가 저장되고 원본과 별도 id로 리스트에 추가됨
- [ ] **클립보드 복사**: 상세 모달 📋 → 스낵바 "복사되었습니다" → 메모장에 붙여넣기 시 섹션별 정렬된 텍스트 확인
- [ ] **스낵바 닫기**: 스낵바 ✕ 버튼으로 수동 닫기 가능

### B-* 역할별 개선 (2026-04-23 신규)
- [ ] **프로필 설정**: 헤더 👤 버튼 클릭 → 모달에서 역할(작성자/검토자/참조자) + 세부 부서 선택 → 저장 → 배지에 이름·부서 표시
- [ ] **프로필 초기화**: 프로필 모달 "초기화" → localStorage에서 제거, 대시보드 상단 미설정 배너 복귀
- [ ] **참조자 읽기 전용**: 프로필=생산팀 또는 KS팩 → 리스트의 ⚡·편집·📑 버튼 숨김, "신규 요청서" 버튼 숨김, "읽기 전용" 배지 노출. 콘솔에서 `openForm()` 직접 호출 시 차단 alert.
- [ ] **공정개발 검토 큐**: 프로필=공정개발팀 → 대시보드에 3개 카드 노출. 카드 클릭 시 리스트 탭으로 이동 + PD 미완만 남고 우선순위순 정렬
- [ ] **부서별 form 탭 자동 열림**: 프로필=연구소로 "+신규 요청서" → 벌크 제조 탭이 기본으로 열림. 공정개발=진행사항 업데이트. 마케팅=기본 정보.
- [ ] **작성자 자동 채움**: 프로필=마케팅·홍길동 → form 열면 부서="마케팅", 영업담당="홍길동" 자동 입력. 공정개발 프로필은 공정개발 담당자 필드.
- [ ] **해외영업 수출 섹션**: 프로필=해외영업 → form에 🌍 수출 정보 섹션 노출. 국가/인허가(멀티)/번역/이슈 입력 후 저장 → 상세 모달에 "🌍 수출 정보" 섹션 표시
- [ ] **수출 섹션 자동 노출**: 기존 xp 데이터 있는 요청서 편집 시 프로필 무관하게 수출 섹션 자동 노출
- [ ] **섹션별 편집자 표시**: 서로 다른 프로필로 동일 요청서 편집 (예: 마케팅이 기본 섹션 저장 → 연구소로 프로필 변경 후 벌크 섹션만 수정 저장) → 상세 모달에 섹션별 "✍ 편집: 이름/부서 · 날짜" 서로 다르게 표시
- [ ] **우선순위 정렬**: 리스트 탭 정렬 드롭다운 → "검토 우선순위순" → 긴급·지연·PD 미완 건이 상단. "시생산 예정일순" → 임박 건 상단.
- [ ] **라인 드롭다운**: 요청서 편집 → 공정개발 기입 섹션 → 생산라인 드롭다운 선택 → 직접 입력 필드 자동 채움. OTHER 선택 시 직접 입력 비움 (수동 입력 가능).
- [ ] **CAPA OK/NG**: 명시적 "NG" 선택 시 리스트의 라인/CAPA 컬럼에 빨간 경고로 표시되는지 (기존 휴리스틱 대신 명시값 우선)
- [ ] **PD 의견 타임라인**: 진행사항 업데이트에 stage="공정 검토" 또는 author에 "공정개발" 포함한 항목이 있는 요청서 → 상세 모달에 "🛠 공정개발 의견 이력" 섹션 자동 추가 (파란 border-left)
- [ ] **SSO 호환성 확인**: profile.email 입력 후 저장 → localStorage의 `cosmax_pilot_profile_v1` JSON에 `role/dept/name/email/org` 키 모두 포함됐는지 DevTools에서 확인
