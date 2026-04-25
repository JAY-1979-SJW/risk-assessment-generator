# 안전서류 93종 catalog / 90종 effective 디렉토리 마이그레이션 계획

> 기준일: 2026-04-25 (정합성 보정 반영)  
> 목적: 향후 디렉토리 분할 시점에 무중단 이동·import 깨짐 방지 절차 사전 확정  
> 범위: **이번 단계는 실제 파일 이동 X** — 절차·임계점·롤백 전략만 문서화  
> 연계: `safety_directory_architecture.md`, `safety_document_db_model.md`

## 0. 기준 수치 (정합성 보정)

| 지표 | 값 | 비고 |
|------|---:|------|
| catalog_total | 93 | OUT 포함 |
| effective_total | 90 | 구현 대상 |
| out_total | 3 | TS-001~003 |
| builder_file_count | 29 | 현재 평면 (M1 트리거 임계점 = 50) |
| evidence_file_count | 67 | 현재 평면 (M2 트리거 임계점 = 100) |
| smoke_test_loc | 4845 | 현재 단일 파일 (M3 트리거 임계점 = 10000) |
| package_count | 7 | 현재 (M4 트리거 임계점 = 10) |

---

## 1. 마이그레이션 트리거 (임계점) — 개별 분리

다음 임계점은 **각각 독립적으로 평가**. 어느 한쪽이 먼저 도달하면 해당 Phase만 단독 실행.  
도달 전에는 **현 평면 구조 유지**.

| 단계 | 대응 Phase | 트리거 임계점 | 현재 상태 | 거리 | 독립 실행 가능 |
|------|----------|-------------|---------|------|:----:|
| **M1** | Phase 1-A | builder 파일 50개 초과 | 29개 | 21개 추가 시 | ✓ |
| **M2** | Phase 1-B | evidence 파일 100개 초과 | 67개 | 33개 추가 시 | ✓ |
| **M3** | Phase 2 | smoke_test 단일 파일 1만줄 초과 | 4845줄 | 5155줄 추가 시 | ✓ |
| **M4** | Phase 3 | 패키지 10개 초과 | 7개 | 3개 추가 시 | ✓ |
| **M5** | Phase 4 | document_catalog.yml 5000줄 초과 | 약 2000줄 | 3000줄 추가 시 | △ (신중) |

> **중요**: Phase 1-A(builder 분리)와 Phase 1-B(evidence 분리)는 **독립 트리거**.  
> M1만 도달하고 M2 미도달이어도 Phase 1-A만 단독 실행 가능 (반대도 동일).

---

## 2. 지금 당장 이동하지 않을 파일 (현행 유지)

### 2.1 절대 이동 금지 (Phase 0 — 즉시)

| 경로 | 이동 금지 이유 |
|------|---------|
| `data/masters/safety/documents/document_catalog.yml` | 단일 진실 소스. 분할 시 추천 엔진·audit·smoke_test 동시 충돌 |
| `engine/output/form_registry.py` | 단일 dispatcher. 위치 변경 시 30+ import 경로 재작성 |
| `engine/recommendation/document_recommender.py` | 추천 엔진 anchor. 외부 호출자 다수 (backend/, scripts/) |
| `data/masters/safety/mappings/*.yml` | 9개 mapping 분리는 이미 적정. 추가만 허용 |
| 모든 evidence JSON 67개 | 명명 규칙(`{DOC_ID}-{TYPE}{N}_*.json`) 일관성 유지 |

### 2.2 이동 보류 (현 평면 유지)

| 경로 | 사유 |
|------|------|
| `engine/output/*_builder.py` 30개 | M1 임계점(50개) 미도달 |
| `data/evidence/safety_law_refs/*.json` 67개 | M2 임계점(100개) 미도달 |
| `scripts/smoke_test_p1_forms.py` 4845줄 | M3 임계점(1만줄) 미도달 |
| `_V11_PACKAGE_RULES` (recommender 내장) | M4 임계점(10개) 미도달 |

---

## 3. 나중에 이동할 파일 (단계별)

### 3.1 M1 — builder 50개 초과 시

**대상**: `engine/output/*_builder.py`  
**이동 후**: `engine/output/builders/{category}/*_builder.py`

| 카테고리 폴더 | 이동 대상 (현 30개 분포) |
|------------|---------------------|
| `builders/wp/` | excavation_workplan, heavy_lifting_workplan, tower_crane_workplan, mobile_crane_workplan, vehicle_workplan, material_handling_workplan, electrical_workplan, confined_space_workplan, formwork_shoring_workplan |
| `builders/ptw/` | confined_space_permit, hot_work_permit, work_at_height_permit, electrical_work_permit, lifting_work_permit |
| `builders/cl/` | scaffold_installation_checklist, formwork_shoring_installation_checklist, construction_equipment_daily_checklist, electrical_facility_checklist, fire_prevention_checklist, tower_crane_self_inspection_checklist, fall_protection_checklist, confined_space_checklist |
| `builders/ed/` | education_log, special_education_log, manager_job_training_record |
| `builders/ra/` | form_excel_builder (RA-001), tbm_log |
| `builders/hm/` | work_environment_measurement, special_health_examination |
| `builders/_common/` | (신규) generic builder 공통 모듈 |

### 3.2 M2 — evidence 100개 초과 시

**대상**: `data/evidence/safety_law_refs/*.json`  
**이동 후**: `data/evidence/safety_law_refs/{category}/*.json`

| 카테고리 폴더 | 이동 대상 |
|------------|---------|
| `safety_law_refs/ptw/` | PTW-002-*, PTW-003-*, PTW-004-*, PTW-007-* (현 25개) |
| `safety_law_refs/cl/` | CL-001-*, CL-002-*, ... CL-007-* (현 17개) |
| `safety_law_refs/wp/` | WP-005-*, WP-011-*, WP-015-* (현 8개) |
| `safety_law_refs/ed/` | ED-003-*, ED-004-* (현 7개) |
| `safety_law_refs/hm/` | HM-001-*, HM-002-* (현 2개) |
| `safety_law_refs/elec/` | ELEC-001-* 공통 pack (현 6개) |
| `safety_law_refs/_misc/` | EDU_CONSTRUCTION_BASIC, worker_licenses 등 |

### 3.3 M3 — smoke_test 1만줄 초과 시

**대상**: `scripts/smoke_test_p1_forms.py`  
**이동 후**: `scripts/smoke_tests/{category}/test_{doc_id}.py`

```
scripts/smoke_tests/
├── __init__.py
├── runner.py                       # run_smoke_test() — 모든 test 통합
├── ptw/
│   ├── test_ptw002.py              # run_ptw002_smoke_test()
│   ├── test_ptw003.py
│   ├── test_ptw004.py
│   └── test_ptw007.py
├── cl/
│   ├── test_cl001.py
│   ├── test_cl002.py
│   └── ...
├── wp/
│   ├── test_wp005.py
│   ├── test_wp011.py
│   └── test_wp015.py
└── ...
```

### 3.4 M4 — 패키지 10개 초과 시

**대상**: `engine/recommendation/document_recommender.py`의 `_V11_PACKAGE_RULES` 상수  
**이동 후**: `data/masters/safety/packages/work_packages.yml` (마스터 외부화)

```yaml
# data/masters/safety/packages/work_packages.yml
packages:
  - code: hot_work
    name_ko: 화기작업
    work_types: [hot_work]
    required: [RA-001, RA-004, PTW-002]
    conditional_required: [CL-005]
    optional: [PPE-001]
  - code: work_at_height
    ...
```

### 3.5 M5 — catalog 5000줄 초과 시 (장기, 신중)

**대상**: `data/masters/safety/documents/document_catalog.yml`  
**이동 후**: `data/masters/safety/documents/by_category/{cat}.yml` + `documents/_index.yml`

> ⚠️ **신중 평가 필요**: 카탈로그 분할 시 추천 엔진·audit·smoke_test 모두 영향. M1~M4 완료 후 재평가.

---

## 4. import 깨짐 방지 전략

### 4.1 핵심 원칙

> **"공개 import 경로는 절대 변경하지 않는다."**  
> 내부 파일이 이동되어도 외부 호출자 코드는 수정 없이 동작해야 한다.

### 4.2 전략 A: re-export (적극 활용)

**적용 대상**: `engine/output/*_builder.py` → `engine/output/builders/{cat}/*.py` 이동 시

#### Before (현재)
```python
# engine/output/form_registry.py
from engine.output.fire_prevention_checklist_builder import build_fire_prevention_checklist_excel
```

#### After (M1 적용 후)

**Step 1**: 실제 파일은 카테고리 폴더로 이동
```
engine/output/builders/cl/fire_prevention_checklist_builder.py
```

**Step 2**: `engine/output/`에 shim 파일 추가 (re-export)
```python
# engine/output/fire_prevention_checklist_builder.py (shim)
"""
호환성 shim — 실제 구현은 engine/output/builders/cl/로 이동.
신규 코드는 builders 경로를 직접 import 권장.
"""
from engine.output.builders.cl.fire_prevention_checklist_builder import (
    build_fire_prevention_checklist_excel,
)

__all__ = ["build_fire_prevention_checklist_excel"]
```

**Step 3**: form_registry.py·외부 호출자는 **수정 불필요** (기존 import 그대로 동작)

#### 검증
- `python scripts/validate_form_registry.py` — PASS 유지
- `python scripts/smoke_test_p1_forms.py` — PASS 유지
- import 추적: `grep -r "from engine.output" .` — 모든 경로 응답

### 4.3 전략 B: alias (yaml 경로 변경 시)

**적용 대상**: `_V11_PACKAGE_RULES` → `data/masters/safety/packages/work_packages.yml` 이동 시

```python
# engine/recommendation/document_recommender.py
def _load_package_rules() -> dict:
    """패키지 규칙 로더 — yaml 외부화 후에도 동일 dict 반환."""
    yaml_path = pathlib.Path("data/masters/safety/packages/work_packages.yml")
    if yaml_path.exists():
        with open(yaml_path, encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return {p["code"]: {
            "required":             p.get("required", []),
            "conditional_required": p.get("conditional_required", []),
            "optional":             p.get("optional", []),
        } for p in data["packages"]}
    # 폴백: 기존 내장 dict
    return _V11_PACKAGE_RULES_LEGACY

_V11_PACKAGE_RULES = _load_package_rules()
```

- 외부 호출자: `from engine.recommendation.document_recommender import _V11_PACKAGE_RULES` 그대로 동작

### 4.4 전략 C: glob 경로 변경 (evidence 분할 시)

**적용 대상**: `data/evidence/safety_law_refs/*.json` → 카테고리 폴더 이동 시

#### Before
```python
EV_DIR = "data/evidence/safety_law_refs"
for fname in os.listdir(EV_DIR):
    if fname.endswith(".json"): ...
```

#### After (재귀 glob)
```python
import glob
EV_DIR = "data/evidence/safety_law_refs"
for fpath in glob.glob(f"{EV_DIR}/**/*.json", recursive=True):
    ...
```

- audit_safety_90_completion.py만 1줄 수정 (`os.listdir` → `glob.glob`)
- evidence 파일명 규칙(`{DOC_ID}-{TYPE}{N}_*.json`) 유지 → document_id 추출 로직 무수정

### 4.5 전략 D: 절대 import 강제 (신규 코드)

```python
# 권장
from engine.output.builders.cl.fire_prevention_checklist_builder import build_fire_prevention_checklist_excel

# 비권장 (상대 import — 이동 시 깨짐)
from .fire_prevention_checklist_builder import build_fire_prevention_checklist_excel
```

---

## 5. registry 경로 변경 전략

### 5.1 form_registry.py 자체는 이동하지 않음

`form_registry.py`는 anchor — 위치 변경 시 backend/, scripts/, tests/ 전부 영향.

### 5.2 import 경로만 단계적으로 갱신

#### Phase A (M1 직후)
```python
# engine/output/form_registry.py
# 기존 import 유지 (shim이 처리)
from engine.output.fire_prevention_checklist_builder import build_fire_prevention_checklist_excel
```

#### Phase B (M1 + 6개월 후, shim 제거)
```python
# engine/output/form_registry.py
# 신규 경로로 직접 import
from engine.output.builders.cl.fire_prevention_checklist_builder import build_fire_prevention_checklist_excel
```

#### Phase C (shim 제거)
- `engine/output/*_builder.py` shim 파일 일괄 삭제
- 사전 검증: `grep -r "from engine.output\.\w*_builder" .` 결과 0건 확인

---

## 6. smoke test 경로 변경 전략

### 6.1 현재 단일 파일 유지 원칙

`scripts/smoke_test_p1_forms.py`는 1만줄 초과 전까지 단일 파일 유지.

### 6.2 분할 시 점진 이전 (M3 도달 시)

#### Step 1: runner 분리
```python
# scripts/smoke_tests/runner.py
def run_smoke_test():
    """카테고리별 smoke test 모두 호출."""
    results = []
    from scripts.smoke_tests.ptw.test_ptw002 import run_ptw002_smoke_test
    from scripts.smoke_tests.cl.test_cl005 import run_cl005_smoke_test
    # ... 각 카테고리 import
    results.extend(run_ptw002_smoke_test())
    results.extend(run_cl005_smoke_test())
    # ... 통합 출력
```

#### Step 2: 기존 entrypoint shim
```python
# scripts/smoke_test_p1_forms.py (shim)
"""호환성 shim — 실제 구현은 scripts/smoke_tests/로 이동."""
from scripts.smoke_tests.runner import run_smoke_test

if __name__ == "__main__":
    run_smoke_test()
```

#### Step 3: CI / 자동 감사 명령어 무수정
- 기존: `python scripts/smoke_test_p1_forms.py`
- shim 덕에 동일하게 동작

---

## 7. 단계별 마이그레이션 순서

### Phase 0 — 현재 (이번 작업)

- ✅ 디렉토리 표준 설계 문서화
- ✅ DB 논리 모델 문서화
- ✅ 마이그레이션 계획 문서화
- ⛔ **실제 파일 이동 없음**
- ⛔ **기존 코드 수정 없음**

### Phase 1-A — M1 도달 시 (builder 파일 50개 초과) — **독립 실행 가능**

**전제**: `safety_directory_architecture.md` 정책 3.5에 따라 신규 builder는 이미 `engine/output/builders/{cat}/`에 저장되어 있을 수 있음. 본 Phase는 **기존 평면 builder의 일괄 이동**.

| 순서 | 작업 | 검증 |
|------|------|------|
| 1A.1 | `engine/output/builders/__init__.py` + `engine/output/builders/{cat}/__init__.py` 일괄 생성 (이미 있으면 skip) | — |
| 1A.2 | 평면 builder 1개를 신규 경로로 이동 + 평면 위치에 shim 파일 작성 | `validate_form_registry.py` PASS |
| 1A.3 | 해당 builder의 smoke_test로 회귀 검증 | `smoke_test_p1_forms.py` PASS |
| 1A.4 | 나머지 평면 builder 카테고리별로 일괄 이동 + shim 일괄 생성 | 모든 검증 스크립트 PASS |
| 1A.5 | form_registry.py import 경로를 신규 경로로 일괄 갱신 (선택, shim 제거 전 단계) | `validate_form_registry.py` PASS |

**완료 기준**: 평면 위치에는 shim 파일만 남고 실제 builder는 모두 카테고리 폴더에 위치.

---

### Phase 1-B — M2 도달 시 (evidence 파일 100개 초과) — **독립 실행 가능**

**전제**: 신규 evidence는 이미 `data/evidence/safety_law_refs/{cat}/`에 저장되고 audit script glob도 재귀로 변경된 상태일 수 있음. 본 Phase는 **기존 평면 evidence의 일괄 이동**.

| 순서 | 작업 | 검증 |
|------|------|------|
| 1B.1 | `data/evidence/safety_law_refs/{cat}/` 카테고리 폴더 일괄 생성 (이미 있으면 skip) | — |
| 1B.2 | audit script가 재귀 glob을 쓰는지 확인 (정책 3.5.2). 평면이면 1줄 변경 | `audit_safety_90_completion.py` evidence 카운트 동일 |
| 1B.3 | 평면 evidence 1개를 카테고리 폴더로 이동 | audit 카운트 + smoke_test PASS |
| 1B.4 | 나머지 평면 evidence 일괄 이동 (카테고리별) | 모든 검증 스크립트 PASS |
| 1B.5 | catalog의 `evidence_file:` 경로 필드를 신규 경로로 일괄 갱신 | catalog 무결성 검증 |

**완료 기준**: 평면 위치(`data/evidence/safety_law_refs/*.json`)에는 evidence 파일이 0개. 모두 카테고리 폴더에 위치.

> **Phase 1-A와 1-B는 서로 의존 없음** — 어느 쪽이든 먼저 실행 가능.

---

### Phase 2 — M3 도달 시 (smoke_test 1만줄)

| 순서 | 작업 | 검증 |
|------|------|------|
| 2.1 | `scripts/smoke_tests/runner.py` 작성 | `python scripts/smoke_tests/runner.py` 실행 |
| 2.2 | 카테고리별 test 파일 분리 | 각 함수 단독 호출 검증 |
| 2.3 | `smoke_test_p1_forms.py`를 shim으로 전환 | 기존 명령어 동작 |

### Phase 3 — M4 도달 시 (패키지 10개)

| 순서 | 작업 | 검증 |
|------|------|------|
| 3.1 | `data/masters/safety/packages/work_packages.yml` 작성 | YAML 파싱 |
| 3.2 | document_recommender.py에 yaml 로더 추가 + 폴백 | `validate_document_recommender.py` PASS |
| 3.3 | `_V11_PACKAGE_RULES_LEGACY`로 이름 변경 후 yaml 우선 사용 | 동일 |
| 3.4 | yaml 단독 동작 확인 후 LEGACY 제거 | 회귀 검증 |

### Phase 4 — 운영 DB 도입 시

| 순서 | 작업 | 비고 |
|------|------|------|
| 4.1 | P1 **7개** 테이블 DDL 작성 | safety_document_db_model.md 참조 (총 13개 + 연결 1개 = 14개) |
| 4.2 | YAML → DB 동기화 스크립트 | `scripts/sync/sync_catalog_to_db.py` |
| 4.3 | API에서 DB 우선 read, YAML fallback | backend/ 신규 |
| 4.4 | P2 **5개** (safety_project_work_activity 포함) 테이블 단계적 도입 | 패키지·관계·활동 외부화 시 |
| 4.5 | P3 **1개** safety_document_audit_result 테이블 도입 | CI 자동 감사 통합 시 |

---

## 8. 롤백 전략

### 8.1 단일 builder 롤백

```bash
# Phase 1.4 중 한 builder 이동 후 검증 실패 시
git revert <move-commit>
git revert <shim-commit>
```

### 8.2 전체 카테고리 롤백

```bash
# M1 전면 적용 후 회귀 발생 시
git revert HEAD~10..HEAD  # 전체 이동 커밋 일괄 revert
```

### 8.3 검증 게이트 (이동 후 필수)

```bash
python scripts/validate_form_registry.py     # PASS 필수
python scripts/smoke_test_p1_forms.py        # PASS 필수
python scripts/validate_document_recommender.py  # PASS 필수
python scripts/audit_safety_gap.py           # PASS 필수
python scripts/validate_safety_platform_skeleton.py  # PASS 필수
python scripts/audit_safety_90_completion.py # WARN (미구현 정상) 또는 PASS
```

> 위 6개 중 1개라도 FAIL → 즉시 롤백.

---

## 9. 위험 요소 및 완화

| 위험 | 영향 | 완화 |
|------|------|------|
| shim 누락으로 import 깨짐 | 30+ 호출자 영향 | 이동 후 `grep -r` 확인 + smoke_test 회귀 |
| 평면 폴더와 카테고리 폴더 동시 존재 | 동일 builder 2곳 정의 | shim 파일은 import만 — 함수 정의 금지 |
| YAML 분할 후 다중 파일 충돌 | 추천 엔진 응답 변경 | M5 신중 평가 — 단일 파일 우선 |
| 카테고리 코드 변경 | DB FK 깨짐 | 카테고리 코드는 **불변** 정책 |
| evidence 파일명 변경 | document_id 추출 로직 깨짐 | 명명 규칙 강제 (Phase 0 표준) |

---

## 10. 결론 및 다음 단계

### 10.1 본 단계(Phase 0) 완료 항목

- [x] 디렉토리 표준 설계 (`safety_directory_architecture.md`)
- [x] DB 논리 모델 (`safety_document_db_model.md`)
- [x] 마이그레이션 계획 (본 문서)
- [x] 현재 코드 변경 없음 — 모든 검증 PASS 유지

### 10.2 다음 권장 작업

1. **신규 builder 추가 시**: `safety_directory_architecture.md` 정책 3.5에 따라 카테고리 표준 경로 즉시 사용 (shim 불필요)
2. **신규 evidence 추가 시**: 카테고리 폴더에 즉시 저장 + audit script glob 1줄 변경
3. **M1 임계점 도달 (builder 50개)**: Phase 1-A 단독 트리거 — 기존 평면 builder 일괄 이동 + shim
4. **M2 임계점 도달 (evidence 100개)**: Phase 1-B 단독 트리거 — 기존 평면 evidence 일괄 이동
5. **DB 도입 결정 시**: P1 7개 테이블 DDL 작성 (`safety_document_db_model.md` 참조)

### 10.3 미적용 항목 (의도적)

- 기존 평면 builder 이동 — M1 임계점 미도달
- 기존 평면 evidence 이동 — M2 임계점 미도달
- shim 파일 작성 — 기존 파일 이동 시점에 동시 작성
- DB DDL 작성 — 운영 시작 시
- audit_safety_90_completion.py glob 변경 — 신규 evidence를 카테고리 폴더에 처음 저장하는 시점에 동시 적용 (지금 X)

---

*생성: 2026-04-25 / 다음 검토: M1 또는 M2 임계점 도달 시*
