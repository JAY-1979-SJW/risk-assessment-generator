# Form Builder Registry 설계

**작성일**: 2026-04-24  
**파일**: `engine/output/form_registry.py`  
**상태**: v1.0 — export API 연결 전 단계

---

## 1. 목적

`education_log_builder.py`와 `workplan_builder.py`를 단일 진입점에서 호출할 수 있도록
form_type 문자열 → builder 함수 디스패치 계층을 제공한다.

export API가 추가될 때 registry만 바라보면 되므로 API 코드가 개별 builder를 직접 import하지 않아도 된다.

---

## 2. 구조

```
engine/output/form_registry.py
├── UnsupportedFormTypeError(ValueError)   # 미지원 form_type 예외
├── FormSpec (frozen dataclass)            # form_type 메타데이터
│     ├── display_name: str
│     ├── builder: Callable[[dict], bytes]
│     ├── required_fields: tuple[str, ...]
│     ├── optional_fields: tuple[str, ...]
│     ├── max_repeat_rows: int | None
│     └── version: str
├── _REGISTRY: dict[str, FormSpec]         # 내부 등록 테이블
└── 공개 API
      ├── supported_types() -> list[str]
      ├── get_spec(form_type) -> FormSpec
      └── build(form_type, form_data) -> bytes
```

---

## 3. 등록된 form_type

### education_log

| 항목 | 값 |
|------|---|
| display_name | 안전보건교육일지 |
| builder | `build_education_log_excel` |
| version | 1.1 |
| max_repeat_rows | 30 (수강자) |
| required_fields | education_type, education_date, education_location, education_duration_hours, education_target_job, instructor_name, instructor_qualification, confirmer_name, confirmer_role |
| optional_fields | site_name, site_address, subjects, attendees, confirm_date |

### excavation_workplan

| 항목 | 값 |
|------|---|
| display_name | 굴착 작업계획서 |
| builder | `build_excavation_workplan_excel` |
| version | 1.0 |
| max_repeat_rows | 10 (안전조치) |
| required_fields | excavation_method, earth_retaining, excavation_machine, soil_disposal, water_disposal, work_method, emergency_measure |
| optional_fields | site_name, project_name, work_location, work_date, supervisor, contractor, safety_steps, sign_date |

---

## 4. 공개 API

```python
# form_type 목록 조회
supported_types() -> list[str]
# → ['education_log', 'excavation_workplan']

# 메타데이터 조회
get_spec("education_log") -> FormSpec
# → FormSpec(display_name='안전보건교육일지', version='1.1', ...)

# xlsx 생성 (디스패치)
build("excavation_workplan", form_data) -> bytes
# 미지원 시 → UnsupportedFormTypeError
```

---

## 5. 오류 처리

| 상황 | 예외 | 메시지 예시 |
|------|------|-----------|
| 미등록 form_type | `UnsupportedFormTypeError(ValueError)` | `지원하지 않는 form_type: 'vehicle_workplan'. 지원 목록: ['education_log', 'excavation_workplan']` |

---

## 6. 신규 form_type 등록 방법

1. builder 모듈 구현 완료 후
2. `_REGISTRY` dict에 `FormSpec` 항목 추가
3. `validate_form_registry.py` — `_EXPECTED_TYPES`와 `_SAMPLES` 갱신
4. 검증 스크립트 재실행 PASS 확인

---

## 7. 제한 사항

| 항목 | 내용 |
|------|------|
| export API 연결 | 이 파일에서 하지 않음 (registry는 순수 매핑/디스패치) |
| DB 스키마 변경 | 없음 |
| required_fields 강제 검증 | registry는 목록만 제공, 강제 검증은 API 레이어 책임 |
| 차량계·터널·해체·중량물 | v1.1 이후 추가 예정 |
