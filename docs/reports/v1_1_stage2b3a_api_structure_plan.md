# V1.1 Stage 2B-3A — 신축공사 API 라우터 구조 설계

작성일: 2026-04-29 (KST)
선행: `docs/reports/v1_1_stage2b2e_server_isolated_dry_run_rerun.md` (PASS)
판정: **PASS (설계 확정, 코드 미변경)**

---

## 1. 기존 API 구조 요약

| 항목 | 현황 |
|---|---|
| 프레임워크 | FastAPI (`backend/main.py`, `app = FastAPI(title="KRAS API", version="2.0.0")`) |
| 라우터 등록 | `app.include_router(<router>, prefix="/api")` 형태로 13개 라우터 등록 (projects, company, organization, assessments, forms, templates, export, engine_results, risk_assessment_draft, risk_assessment, risk_assessment_build, recommend, form_export) |
| 라우터 prefix 관행 | 라우터 자체는 `prefix="/projects"` 등 리소스 단위, 앱 단에서 `/api` 부착 → 최종 `/api/projects/...` |
| DB 접근 | `backend/db.py` psycopg2 helpers: `get_conn / fetchone / fetchall / execute` (RealDictCursor). SQLAlchemy 미사용 |
| 검증 | pydantic v2 BaseModel (`Optional[T]`, dataclass 미혼용) |
| 오류 응답 | `raise HTTPException(status_code, detail)` |
| 인증 | `backend/routers/projects.py` 기준 미적용 (인증 미들웨어/Depends 없음) |
| 스키마 디렉터리 | `backend/schemas/` 존재 (현재 risk_assessment_build, risk_assessment_draft 2개만) |
| repository 계층 | **없음.** 라우터에서 직접 SQL 호출 |

## 2. V1.1 라우터 배치 추천

| 항목 | 결정 |
|---|---|
| 기존 `/api/projects` | **유지** (호환성 유지, 어떤 변경도 없음) |
| 신규 V1.1 base path | `/api/v1/new-construction` |
| 라우터 파일 | `backend/routers/new_construction.py` (단일 파일 시작 — 리소스가 늘면 분리) |
| router prefix | `prefix="/v1/new-construction"`, 앱은 기존 패턴대로 `prefix="/api"` 추가 |
| repository 파일 | `backend/repositories/new_construction_repository.py` (`backend/repositories/__init__.py` 신설) |
| 스키마 파일 | `backend/schemas/new_construction.py` (pydantic 모델: ProjectProfile, SiteCreate/Update, ContractorCreate/Update, WorkerCreate/Update, ProjectEquipmentCreate/Update) |
| DB helper | 기존 `backend/db.py` 재사용. SQLAlchemy 도입 없음 |

이유: 기존 라우터는 V1 위험성평가 도메인 / V1.1은 신축공사 도메인 — 혼합하지 않고 base path로 명확히 분리. 추후 V1 deprecation 시점에도 영향 격리.

## 3. API 엔드포인트 초안 (MVP)

### 3.1 Project profile (V1.1 확장 컬럼 18개 노출)
- `GET    /api/v1/new-construction/projects/{project_id}/profile`
- `PATCH  /api/v1/new-construction/projects/{project_id}/profile`

기존 `/api/projects/{pid}` 와 분리. baseline 컬럼은 기존 라우터, V1.1 확장은 신규 profile 엔드포인트로 응답 분리.

### 3.2 Sites
- `GET    /api/v1/new-construction/projects/{project_id}/sites`
- `POST   /api/v1/new-construction/projects/{project_id}/sites` (201)
- `PATCH  /api/v1/new-construction/sites/{site_id}`
- `DELETE /api/v1/new-construction/sites/{site_id}` (204)

### 3.3 Contractors
- `GET    /api/v1/new-construction/projects/{project_id}/contractors`
- `POST   /api/v1/new-construction/projects/{project_id}/contractors` (201)
- `PATCH  /api/v1/new-construction/contractors/{contractor_id}`
- `DELETE /api/v1/new-construction/contractors/{contractor_id}` (204)

### 3.4 Workers
- `GET    /api/v1/new-construction/projects/{project_id}/workers`
- `POST   /api/v1/new-construction/projects/{project_id}/workers` (201)
- `PATCH  /api/v1/new-construction/workers/{worker_id}`
- `DELETE /api/v1/new-construction/workers/{worker_id}` (204)

### 3.5 Project Equipment (URL은 `equipment`, DB는 `project_equipment`)
- `GET    /api/v1/new-construction/projects/{project_id}/equipment`
- `POST   /api/v1/new-construction/projects/{project_id}/equipment` (201)
- `PATCH  /api/v1/new-construction/equipment/{equipment_id}`
- `DELETE /api/v1/new-construction/equipment/{equipment_id}` (204)

### 3.6 공통 규칙
- 응답: 단건은 객체, 목록은 `{"items": [...]}` (기존 projects는 `{"projects": rows}` 패턴 사용 — V1.1은 일관성을 위해 `items` 키로 표준화)
- 오류: 404 `... not found`, 400 `No fields to update` 등 기존 패턴 답습
- created_at/updated_at: 응답 포함
- 페이지네이션: MVP는 미적용 (정렬 `ORDER BY created_at DESC`)

## 4. Repository / DB helper 사용 방식

```python
# backend/repositories/new_construction_repository.py (예시 시그니처만, 코드 작성은 2B-3B)
def get_project_profile(project_id: int) -> dict | None: ...
def update_project_profile(project_id: int, fields: dict) -> int: ...

def list_sites(project_id: int) -> list[dict]: ...
def create_site(project_id: int, payload: dict) -> int: ...
def update_site(site_id: int, fields: dict) -> int: ...
def delete_site(site_id: int) -> int: ...

# contractors / workers / project_equipment 동일 패턴
```

원칙:
- 라우터는 pydantic 검증 + repository 호출 + HTTPException 매핑만 담당
- repository는 `db.fetchone/fetchall/execute` 직접 호출, SQL을 함수 단위로 캡슐화
- transaction이 한 endpoint 내 다중 statement면 향후 `backend/db.py` 에 `transaction()` 컨텍스트 추가 검토 (MVP 범위 외)

## 5. project_equipment 네이밍 주의사항

- **DB 테이블**: `project_equipment` (V1.1 0018 마이그레이션)
- **URL 경로**: `/equipment` (UX 단순성)
- **pydantic 모델명**: `ProjectEquipmentCreate / ProjectEquipmentUpdate / ProjectEquipmentOut`
- **변수/함수명**: `project_equipment_*`
- **혼동 방지 주석 필수**: 라우터·repository 상단에 다음 주석 명시
  ```
  # NOTE: V1.1 'project_equipment' 테이블만 다룬다.
  #       기존 마스터 'equipment'(equipment_code PK, document_equipment_map FK)와 혼동 금지.
  ```
- 기존 `equipment` 마스터에 대한 SELECT/UPDATE/DELETE 절대 금지 (V1.1 라우터는 read조차 하지 않음)

## 6. 개인정보 / 보안 기준

| 항목 | 기준 |
|---|---|
| 주민번호/외국인등록번호 | 스키마 없음 (저장 금지) |
| worker phone | 0017 마이그레이션에 미포함 — pydantic 모델에도 추가 금지 |
| created_by_user_id | nullable, FK ON DELETE SET NULL — 인증 미적용 환경에서 NULL 허용 |
| 인증/권한 | 기존 라우터에 인증 미들웨어 없음 → V1.1 MVP도 동일 (TODO: Stage 2B 후속에서 일괄 적용 검토) |
| 입력 검증 | pydantic 필수 — VARCHAR 길이/날짜 형식/Enum 허용값(상태·타입) 모두 모델 단계에서 거름 |
| SQL injection | parameterised query 강제 (`%s`), f-string SQL 금지. 동적 컬럼은 화이트리스트 매칭 후 조립 |
| 오류 메시지 | DB 메시지 그대로 노출 금지 — `HTTPException(detail="...")` 로 사용자용 문구만 |

## 7. Stage 2B-3B 구현 범위 (다음 단계)

최소 범위 권장:
1. `backend/repositories/__init__.py`, `backend/repositories/new_construction_repository.py` 신규 (project profile + sites만)
2. `backend/schemas/new_construction.py` 신규 (project profile + sites)
3. `backend/routers/new_construction.py` 신규 — `GET/PATCH project profile` + sites CRUD 4개
4. `backend/main.py` 에 `include_router(new_construction.router, prefix="/api")` 1줄 추가
5. `python -m py_compile backend/routers/new_construction.py backend/repositories/new_construction_repository.py backend/schemas/new_construction.py` 통과
6. 격리 dry-run DB(`kras_v11_dryrun_20260429`)로 수동 호출 검증 (운영 DB 미접근)
7. 단위 테스트는 MVP 후 단계 (2B-3C)

contractors / workers / project_equipment 는 2B-3C 이후 단계로 미룸 (한 단계당 PR 크기 제한).

## 8. 리스크

| # | 리스크 | 완화 |
|---|---|---|
| R1 | URL 의 `/equipment` 가 기존 마스터 의미로 오해될 수 있음 | base path `/v1/new-construction` 로 도메인 명확화 + 코드 주석 강제 |
| R2 | 기존 `/api/projects/{pid}` 응답이 V1.1 확장 컬럼을 그대로 노출 → 클라이언트 호환성 영향 | 기존 라우터 SELECT 변경 금지, V1.1 확장은 별도 `/profile` 엔드포인트만 사용 |
| R3 | repository 도입이 다른 도메인(V1)과의 일관성을 깨뜨림 | repository는 V1.1 전용으로 한정, V1 라우터는 손대지 않음 |
| R4 | 인증 부재로 V1.1 데이터(작업자/업체) 외부 노출 가능 | 운영 배포 전 Stage 2B 후속에서 인증 일괄 적용 — 그 전까지는 사내망/staging 한정 |
| R5 | 운영 DB 에 0013~0023 미적용 — V1.1 라우터가 운영에 배포되면 500 발생 | API 배포 전 운영 DB migration 적용을 별도 단계(Stage 2B-4)로 분리 게이팅 |

---

## 9. 검증

- 코드 변경: 없음
- DB 변경: 없음
- migration 변경: 없음
- registry/catalog/supplementary 변경: 없음
- git diff: 본 보고서 1개
