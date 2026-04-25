# 안전서류 구현 상태 보드 v1.0

**작성일**: 2026-04-24  
**기준**: form_registry.py v1.1 + export API + 커밋 cc0c777 (최신)  
**커버리지**: 3/20건 DONE (15%)

---

## 판정 기준

| 판정 | 정의 |
|------|------|
| **DONE** | builder 파일 + form_registry 등록 + export API 연결 — 3가지 모두 완료 |
| **PARTIAL** | builder 또는 registry 중 하나만 있음 |
| **TODO** | 미구현 (신규 개발 필요) |
| **EXCLUDED** | 전문 문서 / 법정 의무 아님 / v1 범위 제외 |

---

## DONE (3건) — 즉시 사용 가능

### 위험성평가표 (`risk_assessment`)

| 항목 | 내용 |
|------|------|
| form_type | `risk_assessment` |
| builder | `engine/output/form_excel_builder.py` → `build_form_excel()` |
| 입력 스키마 | `kras_standard_form_v1` (`{"header":{}, "rows":[]}`) |
| registry | ✅ 등록됨 (커밋 548ceee, 2026-04-24) |
| API | ✅ `POST /api/forms/export` 연결 완료 |
| 법령 근거 | 산안법 제36조, 고시 제2023-19호 |
| 보존기간 | 3년 |
| 컬럼 수 | 14컬럼 (번호, 공정명, 세부작업명, 위험분류 대/중, 유해위험요인, 관련근거, 현재안전보건조치, 평가척도, 가능성, 중대성, 위험성, 위험성감소대책, 개선후위험성, 개선예정일) |
| 자동채움 | 39% (사업장 마스터 + KRAS DB 연계 시) |

---

### 안전보건교육일지 (`education_log`)

| 항목 | 내용 |
|------|------|
| form_type | `education_log` |
| builder | `engine/output/education_log_builder.py` → `build_education_log_excel()` |
| required_fields | `education_type`, `education_date`, `education_location`, `education_duration_hours`, `education_target_job`, `instructor_name`, `instructor_qualification`, `confirmer_name`, `confirmer_role` (9개) |
| optional_fields | `site_name`, `site_address`, `subjects`, `attendees`, `confirm_date` |
| repeat_field | `attendees` (최대 30행) |
| registry | ✅ 등록됨 (v1.1) |
| API | ✅ `POST /api/forms/export` 연결 완료 |
| 법령 근거 | 산안법 제29조, 시행규칙 제32조 |
| 보존기간 | 3년 |
| 자동채움 | 56% (이전 교육 이력 활용 시) |
| 주의 | 별지 52호의2 원본 미수집 — 법정 레이아웃과 차이 있을 수 있음 |

---

### 굴착 작업계획서 (`excavation_workplan`)

| 항목 | 내용 |
|------|------|
| form_type | `excavation_workplan` |
| builder | `engine/output/workplan_builder.py` → `build_excavation_workplan_excel()` |
| required_fields | `excavation_method`, `earth_retaining`, `excavation_machine`, `soil_disposal`, `water_disposal`, `work_method`, `emergency_measure` (7개) |
| optional_fields | `site_name`, `project_name`, `work_location`, `work_date`, `supervisor`, `contractor`, `safety_steps`, `sign_date` |
| repeat_field | `safety_steps` (최대 10행) |
| registry | ✅ 등록됨 (v1.0) |
| API | ✅ `POST /api/forms/export` 연결 완료 |
| 법령 근거 | 기준규칙 제38조 제1항 제6호, 제82조 |
| 대상 조건 | 굴착면 높이 2m 이상 |
| 자동채움 | 47% (이전 계획서 재사용 시) |
| 누락 필드 | 출입통제, 유도자, 지형·지반 조사, 비상연락망 — 커밋 cc0c777 일부 보완 |

---

## PARTIAL (0건)

> 이전 PARTIAL이었던 위험성평가표는 2026-04-24 커밋 548ceee에서 DONE으로 전환 완료.  
> 현재 PARTIAL 없음.

---

## TODO (17건)

### TODO-A: 별지 수집 완료 — builder만 구현하면 DONE (5건)

법정 별지 원본이 source_map A등급으로 확보되어 레이아웃 참조 즉시 가능.

| doc_id | 서류명 | 수집 별지 | autofill | 난이도 |
|--------|--------|---------|:--------:|:------:|
| ACC-001 | 산업재해조사표 | 별지 제30호 (A) | 21% | ★★★☆☆ |
| MTG-001 | 산업안전보건위원회 회의록 | 별표 제2의2 (A) | 64% | ★★☆☆☆ |
| CON-001 | 유해·위험작업 도급승인 신청서 | 별지 제31·32·33·34호 (A) | 64% | ★★☆☆☆ |
| HRP-001 | 제조업 유해위험방지계획서 | 별지 제16·18·19호 (A) | 60% | ★★★★☆ |
| HRP-002 | 건설공사 유해위험방지계획서 | 별지 제17·22·103호 (A) | 60% | ★★★★☆ |

---

### TODO-B: 별지 없음 — workplan_builder 패턴 확장 (8건)

기준규칙 제38조 작업계획서 계열. `workplan_builder.py` 구조 재사용, 법적 필수 항목만 교체.

| doc_id | 서류명 | 법정 핵심 항목 | autofill | 난이도 | 우선순위 |
|--------|--------|-------------|:--------:|:------:|:-------:|
| WP-002 | 차량계 건설기계 작업계획서 | machine_type, machine_capacity, travel_route, work_method | 65% | ★★☆☆☆ | **P1** |
| WP-003 | 차량계 하역운반기계 작업계획서 | machine_type, machine_max_load, travel_route, work_method | 63% | ★★☆☆☆ | **P1** |
| WP-004 | 타워크레인 작업계획서 | 설치·해체 순서, 작업구역, 안전신호방법, 안전조치 | - | ★★★☆☆ | P2 |
| WP-005 | 중량물 취급 작업계획서 | 중량물 종류·중량, 취급방법, 신호방법, 안전조치 | - | ★★☆☆☆ | P2 |
| WP-006 | 터널 굴착 작업계획서 | 굴착방법, 버럭처리, 지보공, 환기방법 | - | ★★★★☆ | P3 |
| WP-007 | 건축물 해체 작업계획서 | 해체방법·순서, 가설설비, 방호조치 | - | ★★★☆☆ | P3 |
| WP-009 | 거푸집동바리 작업계획서 | 조립·해체 절차, 구조검토, 안전조치 | - | ★★★☆☆ | P4 |
| WP-010 | 교량 건설 작업계획서 | 가설구조물, 양중계획, 안전관리계획 | - | ★★★☆☆ | P4 |

---

### TODO-C: 기타 미구현 (4건)

| doc_id | 서류명 | 상황 | 선행 조건 | 우선순위 |
|--------|--------|------|---------|:-------:|
| RISK-002 | 위험성평가 자체점검표 | 법정 별지 없음, B등급 참조 | B등급 원본 항목 확정 | P4 |
| EDU-002 | 교육훈련 기록부 | 법정 별지 없음, EDU-001과 통합 가능 | EDU-001 안정화 후 검토 | P4 |
| MTG-002 | 노사협의체 회의록 | 별표 31의2 미수집 | 별표 수집 선행 | P3 |
| WP-008 | 화학설비 작업계획서 | 화학 사업장 한정, 전문 항목 多 | 화학 도메인 항목 확정 | P4 |

---

## EXCLUDED (3건) — 영구 제외

| doc_id | 서류명 | 제외 사유 |
|--------|--------|---------|
| PSM-001 | 공정안전보고서 (PSM) | 대규모 화학 사업장 한정, 수백 페이지 보고서 구조 — builder 방식 부적합 |
| REG-001 | 안전보건관리규정 | 규정집 형태 (서식 아님), 업종별 내용 완전 상이 |
| TBM-001 | TBM 일지 | 법정 의무 없음, 자유 형식 — 범위 외 |

---

## 현재 상태 요약 대시보드

```
전체 감사 대상: 20건
────────────────────────────────
DONE        ███░░░░░░░░░░░░░░░░░░  3건 (15%)
TODO        ████████████████████░  17건 (85%)
EXCLUDED    (별도)                  3건
────────────────────────────────
법정 별지 수집 완료 서류 중 builder 미구현: 5건 (즉시 착수 가능)
workplan_builder 패턴 재사용 가능 서류:    8건
```

## API 현황

```
GET  /api/forms/types    → 3종 응답 (education_log, excavation_workplan, risk_assessment)
POST /api/forms/export   → file/base64 모드, 한글 파일명, 5단계 검증
```
