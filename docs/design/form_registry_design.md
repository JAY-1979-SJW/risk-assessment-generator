# Form Builder Registry 설계

**작성일**: 2026-04-24  
**파일**: `engine/output/form_registry.py`  
**상태**: v1.1 — export API 연결 전 단계

---

## 1. 목적

`education_log_builder.py`와 `workplan_builder.py`를 단일 진입점에서 호출할 수 있도록
form_type 문자열 → builder 함수 디스패치 계층을 제공한다.

- builder 선택·호출 외의 어떤 로직도 추가하지 않는다 (최소 구조 원칙).
- export API가 추가될 때 개별 builder를 직접 import하지 않고 registry만 사용한다.
- DB 스키마 변경 없음. 기존 builder 함수 수정 없음.

---

## 2. 구조

```
engine/output/form_registry.py
├── UnsupportedFormTypeError(ValueError)    # 미지원 form_type 예외
├── FormSpec (frozen dataclass)             # form_type 메타데이터
│     ├── form_type: str
│     ├── display_name: str
│     ├── version: str
│     ├── builder: Callable[[dict], bytes]  # 내부 참조 (공개 dict 미포함)
│     ├── required_fields: tuple[str, ...]
│     ├── optional_fields: tuple[str, ...]
│     ├── repeat_field: str | None          # 반복행 list 필드명
│     ├── max_repeat_rows: int | None
│     └── to_dict() -> dict                 # builder 제외 공개 메타데이터
├── _REGISTRY: dict[str, FormSpec]          # 내부 등록 테이블
└── 공개 API
      ├── list_supported_forms() -> list[dict]
      ├── get_form_spec(form_type) -> dict
      └── build_form_excel(form_type, form_data) -> bytes
```

---

## 3. 등록된 form_type

### 3.1 education_log

| 항목 | 값 |
|------|---|
| display_name | 안전보건교육일지 |
| version | 1.1 |
| builder | `build_education_log_excel` |
| repeat_field | `attendees` |
| max_repeat_rows | 30 |
| required_fields | education_type, education_date, education_location, education_duration_hours, education_target_job, instructor_name, instructor_qualification, confirmer_name, confirmer_role (9개) |
| optional_fields | site_name, site_address, subjects, attendees, confirm_date (5개) |

### 3.2 excavation_workplan

| 항목 | 값 |
|------|---|
| display_name | 굴착 작업계획서 |
| version | 1.0 |
| builder | `build_excavation_workplan_excel` |
| repeat_field | `safety_steps` |
| max_repeat_rows | 10 |
| required_fields | excavation_method, earth_retaining, excavation_machine, soil_disposal, water_disposal, work_method, emergency_measure (7개) |
| optional_fields | site_name, project_name, work_location, work_date, supervisor, contractor, safety_steps, sign_date (8개) |

---

## 4. 공개 API

```python
from engine.output.form_registry import (
    list_supported_forms, get_form_spec, build_form_excel
)

# 지원 form_type 목록 조회
list_supported_forms()
# → [
#     {"form_type": "education_log", "display_name": "안전보건교육일지", ...},
#     {"form_type": "excavation_workplan", "display_name": "굴착 작업계획서", ...},
#   ]

# 단일 form_type 메타데이터 조회
get_form_spec("excavation_workplan")
# → {"form_type": "excavation_workplan", "required_fields": [...], ...}

# xlsx 생성 (builder 디스패치)
build_form_excel("education_log", form_data)  # → bytes
```

---

## 5. 오류 처리

| 상황 | 예외 | 비고 |
|------|------|------|
| 미등록 form_type | `UnsupportedFormTypeError(ValueError)` | 지원 목록 메시지 포함 |
| builder가 bytes 반환 안 함 | `TypeError` | 내부 오류 방어 |

---

## 6. 신규 form_type 등록 절차

1. builder 모듈 구현 완료 후
2. `_REGISTRY` dict에 `FormSpec` 항목 추가
3. `validate_form_registry.py` — `_EXPECTED_TYPES`와 `_SAMPLES` 갱신
4. 검증 스크립트 재실행 PASS 확인

---

## 7. 제한 사항

| 항목 | 내용 |
|------|------|
| export API 연결 | 이 파일에서 하지 않음 (registry는 순수 매핑/디스패치) |
| required_fields 강제 검증 | registry는 목록만 제공, 필드 존재 강제는 API 레이어 책임 |
| DB 스키마 | 변경 없음 |
| 차량계·터널·해체·중량물 | v1.1 이후 추가 예정 |
