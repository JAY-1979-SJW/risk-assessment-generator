# V1.1 Stage 2B-4A — 자동생성 Rule MVP 설계

작성일: 2026-04-29 (KST)
선행: `docs/reports/v1_1_stage2b3f_api_live_smoke.md` (PASS)
판정: **PASS (설계 확정, 코드/DB 무변경)**

---

## 1. Rule MVP 전체 요약

V1.1 MVP에서 자동생성을 도입할 3개 Rule을 확정하고, 본 단계에서는 코드 구현 없이 라우팅·메타데이터 흐름·문서 매핑만 설계한다.

| Rule ID | 이름 | 트리거 source | 핵심 SafetyEvent |
|---|---|---|---|
| `RULE_NEW_WORKER` | 신규 근로자 등록 | `workers` POST + 명시 호출 | `worker_registered` |
| `RULE_EQUIPMENT_INTAKE` | 장비 반입 등록 | `project_equipment` POST + 명시 호출 | `equipment_registered` |
| `RULE_DAILY_TBM` | 매일 TBM | 일자 + 명시 호출 | `daily_tbm` |

전략 요약:
- **명시 실행 우선** — V1.1은 worker/equipment POST가 자동으로 패키지를 만들지 않는다. 사용자/프론트엔드가 `preview` → `generate` 두 단계를 명시적으로 호출.
- **메타 우선** — Stage 2B-4A/4B 까지는 `document_generation_jobs` / `generated_document_packages` / `generated_document_files` 메타만 적재. 실제 Excel/ZIP/다운로드는 Stage 2B-5 이후.

## 2. Rule 3개 상세 정의 (registry 키 매핑 확인 완료)

### 2.1 `RULE_NEW_WORKER`

| 코드 | 라벨 | document_kind | registry 키 |
|---|---|---|---|
| ED-001 | 안전보건교육 교육일지 | form | `education_log` |
| PPE-001 | 보호구 지급 대장 | form | `ppe_issuance_ledger` |
| — | 출근부/배치부(첨부) | supplemental | `attendance_roster` |
| — | 보호구 수령 확인서 | supplemental | `ppe_receipt_confirmation` |
| — | 문서 첨부 리스트 | supplemental | `document_attachment_list` |

필요 입력: `worker.id`, `worker_name`, `trade`, `first_work_date`, `contractor_id`, `project.title`, `project.site_address`.
누락 가드: `first_work_date is None` → preview 시 missing 필드로 표시.

### 2.2 `RULE_EQUIPMENT_INTAKE`

| 코드 | 라벨 | document_kind | registry 키 |
|---|---|---|---|
| PPE-002 | 건설 장비 반입 신청서 | form | `construction_equipment_entry_request` |
| PPE-003 | 건설 장비 보험·정기검사증 확인서 | form | `equipment_insurance_inspection_check` |
| CL-003 | 건설 장비 일일 사전 점검표 | form | `construction_equipment_daily_checklist` |
| — | 운전원 자격증 확인서 | supplemental | `equipment_operator_qualification_check` |
| — | 문서 첨부 리스트 | supplemental | `document_attachment_list` |
| — | 사진 첨부 시트 | supplemental | `photo_attachment_sheet` |

필요 입력: `project_equipment.id`, `equipment_name`, `equipment_type`, `registration_no`, `entry_date`, `operator_name`, `contractor_id`.
누락 가드: `operator_qualification_checked == False` → preview 단계에서 경고만, generate 차단은 V2.0에서 결정.

### 2.3 `RULE_DAILY_TBM`

| 코드 | 라벨 | document_kind | registry 키 |
|---|---|---|---|
| RA-004 | TBM 일지 | form | `tbm_log` |
| DL-005 | 작업 전 안전 확인서 | form | `pre_work_safety_check` |
| — | 출근부 | supplemental | `attendance_roster` |
| — | 사진 첨부 시트 | supplemental | `photo_attachment_sheet` |

필요 입력: `event_date`(=TBM 일자), `project.id`, `work_schedules` 중 해당 일 진행 항목, `workers.status='active'` 카운트.

## 3. preview / generate API 설계

### 3.1 Rule 목록

```
GET /api/v1/new-construction/rules
→ 200
{ "items": [
    { "rule_id": "RULE_NEW_WORKER",
      "display_name": "신규 근로자 등록 패키지",
      "trigger_event_type": "worker_registered",
      "documents": [ {kind, key, label, code}, ... ] },
    ...
] }
```

### 3.2 Preview (DB 쓰기 없음)

```
POST /api/v1/new-construction/projects/{project_id}/rules/{rule_id}/preview
body: { "subject_id": <int>?,           # worker_id / equipment_id
        "event_date": "YYYY-MM-DD"?,    # daily_tbm
        "context": {...}? }
→ 200
{
  "rule_id": "...",
  "project_id": ...,
  "subject": { "kind": "worker"|"equipment"|"date", "id": ... },
  "documents": [
    { "kind": "form", "key": "education_log", "label": "안전보건교육 교육일지",
      "code": "ED-001", "ready": true, "missing_fields": [] },
    ...
  ],
  "ready": false,
  "missing_fields": ["worker.first_work_date", ...]
}
```

- 순수 read. DB 변경/INSERT 없음.
- 누락 필드 검사는 Rule 별 입력 명세에 따라 수행.
- `ready = all(doc.ready)`.

### 3.3 Generate metadata (Excel 미생성)

```
POST /api/v1/new-construction/projects/{project_id}/rules/{rule_id}/generate
body: { "subject_id": ..., "event_date": "...?", "user_id": ...?, "force": false }
→ 201
{
  "rule_id": "...",
  "package_id": <int>,
  "job_id": <int>,
  "file_ids": [<int>, ...],
  "status": "pending",
  "expected_documents": N
}
```

서버 처리:
1. preview 와 동일한 입력 검증 (`force=false` 일 때 `ready=false` 면 400).
2. `safety_events` 1건 INSERT (`event_type` = Rule mapping, `payload_json` = subject summary).
3. `document_generation_jobs` 1건 INSERT (`status='pending'`, `job_type='package'`, `safety_event_id` 연결, `input_snapshot_json` = §6 스냅샷).
4. `generated_document_packages` 1건 INSERT (`status='created'`, `rule_id`, `package_type`, `generation_job_id` 연결, `document_count = N`).
5. 각 문서별 `generated_document_files` INSERT (form/supplemental 별로 `document_kind`/`form_type`/`supplemental_type`/`display_name` 채움, `status='created'`, `file_path/file_size/mime_type` 미채움).

본 단계 이후에도 Excel 생성/ZIP 압축은 Stage 2B-5 이후 별도 워커가 `status` 를 `running → ready` 로 갱신하는 모델로 진행.

## 4. metadata 생성 흐름 다이어그램 (text)

```
client                            FastAPI                      DB
  │  POST /rules/{r}/generate ───▶ rule_engine.preview()
  │                                  │ (read only)
  │                                  ├─ project / worker(or eq)
  │                                  └─ ready? missing?
  │                                  │
  │                                  ├─▶ safety_events INSERT
  │                                  ├─▶ document_generation_jobs INSERT
  │                                  ├─▶ generated_document_packages INSERT
  │                                  └─▶ generated_document_files INSERT (N건)
  │  ◀─── 201 + ids
  ...
  (Stage 2B-5+) builder worker ──▶ files.status = ready, file_path 등 갱신
```

## 5. input_snapshot_json 설계 (모든 Rule 공통 envelope)

```jsonc
{
  "rule_id": "RULE_NEW_WORKER",
  "rule_version": "1.1.0",
  "generated_at": "2026-04-29T12:34:56+09:00",
  "subject": { "kind": "worker", "id": 42, "summary": {...} },
  "project": { "id": 1, "title": "...", "site_address": "...", "construction_type": "..." },
  "context": { "event_date": null, "options": {...} },
  "included_documents": [
    { "kind": "form", "key": "education_log", "code": "ED-001" },
    ...
  ]
}
```

- subject.summary 에는 worker/equipment 의 read-only 요약만(주민/외국인등록·연락처 등 민감 필드 제외).
- 향후 재생성 시 동일 스냅샷으로 결정적 결과를 만들 수 있게 한다.

## 6. 상태값 정책

| 단계 | document_generation_jobs | generated_document_packages | generated_document_files |
|---|---|---|---|
| generate (메타만) | `pending` | `created` | `created` |
| (Stage 2B-5) builder 시작 | `running`, `started_at=now()` | `generating` | `created` |
| 빌더 완료 | `completed`, `finished_at=now()` | `ready` | `ready`, `file_path/file_size/mime_type` 채움 |
| 실패 | `failed`, `error_message` | `failed` | `failed` |
| 취소 | `cancelled` | `cancelled` | (별도 갱신 없음) |

## 7. 코드 구조 제안 (구현은 Stage 2B-4B)

```
backend/services/new_construction_rules.py     # 신규
  ├─ RULE_DEFINITIONS: dict[str, RuleSpec]    # 코드 상수
  │   ├─ RULE_NEW_WORKER
  │   ├─ RULE_EQUIPMENT_INTAKE
  │   └─ RULE_DAILY_TBM
  ├─ list_rules() -> list[dict]
  ├─ preview(project_id, rule_id, payload) -> dict
  └─ generate(project_id, rule_id, payload) -> dict
       └─ writes via repository helpers (no direct SQL)

backend/repositories/new_construction_repository.py  # 확장
  └─ create_rule_package_metadata(...)   # 트랜잭션 격리(가능 시)

backend/schemas/new_construction.py     # 추가 모델
  ├─ RulePreviewRequest / RulePreviewResponse
  ├─ RuleGenerateRequest / RuleGenerateResponse
  └─ RuleListResponse

backend/routers/new_construction.py     # 라우트 3개 추가
  ├─ GET    /rules
  ├─ POST   /projects/{pid}/rules/{rule_id}/preview
  └─ POST   /projects/{pid}/rules/{rule_id}/generate
```

원칙:
- **Rule 정의는 코드 상수**로 시작. DB rule 테이블은 V1.1 미도입.
- 트랜잭션: generate 4건 INSERT는 한 connection 내 manual `BEGIN/COMMIT` 으로 묶거나, 실패 시 일부 적재 롤백 가능하게 `db.py` 에 가벼운 helper 추가 검토 (Stage 2B-4B 첫 작업).
- `form_registry` / `supplementary_registry` 는 read-only 로 import. registry 자체 수정 금지.

## 8. Stage 2B-4B 구현 범위 (다음 단계)

1. `backend/services/new_construction_rules.py` 신규 — 3 Rule 상수 + preview/generate 함수.
2. `backend/repositories/new_construction_repository.py` 에 `create_rule_package_metadata(...)` (4테이블 일괄 INSERT) 추가.
3. `backend/schemas/new_construction.py` — Rule 4개 모델 추가.
4. `backend/routers/new_construction.py` — 라우트 3개 추가.
5. py_compile + 격리 DB live smoke 추가 (preview/generate 12개 케이스 정도, 기존 smoke 흐름에 부착).

미포함(엄격 배제): Excel builder 호출, ZIP 생성, 파일 저장, 다운로드, registry 수정, 운영 DB DDL/마이그레이션.

## 9. 리스크 / 금지사항

| # | 리스크 | 완화 |
|---|---|---|
| R1 | preview 가 read-only 라는 보장이 깨질 가능성 | services 모듈에서 INSERT 호출을 import-time linter로 검증 (단순 grep), PR 시 확인 |
| R2 | generate 가 부분 적재 실패로 고아 row 발생 | repository에 한 connection / explicit BEGIN/COMMIT, 실패 시 ROLLBACK |
| R3 | Rule 정의가 코드 상수라 변경 시 배포 필요 | V1.1 의도대로 수용 — 운영 안정성 우선, V2.0에서 DB 기반 검토 |
| R4 | registry 키 변경/제거 시 Rule 깨짐 | services 모듈 import 시 키 존재 검증 어서션 추가 (Stage 2B-4B) |
| R5 | event_type 가 Literal whitelist (`worker_registered/equipment_registered/daily_tbm`) 와 정확히 일치해야 함 | RuleSpec.event_type 을 Literal 과 동일 상수로 매핑 |

금지(반복): Excel/ZIP/다운로드 구현, 자동 트리거(POST 즉시 패키지 생성), document_catalog.yml 수정, registry 수정, builder 수정, UI 구현.

---

## 10. 검증

- 코드 변경: 없음
- DB 변경: 없음
- migration 변경: 없음
- registry/catalog/supplementary 변경: 없음
- git diff: 본 보고서 1개
