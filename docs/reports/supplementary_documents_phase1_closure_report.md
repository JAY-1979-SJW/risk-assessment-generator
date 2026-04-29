# 1차 부대서류 LIVE 마감 보고서

**작성일**: 2026-04-29  
**대상**: supplementary_registry.py 등록 부대서류 1차 패키지 (10종)  
**최종 판정**: **PASS — 전종 LIVE 마감**

---

## 1. 전체 요약

| 항목 | 결과 |
|------|------|
| supplementary_registry 등록 | **10종** |
| LIVE (builder 구현 완료) | **10종** |
| TODO (미구현) | **0종** |
| main form_registry | **87건 (변경 없음)** |
| document_catalog.yml | **변경 없음** |
| audit 최종 판정 | **PASS** (87종, FAIL 0) |
| smoke 테스트 | **3종 OK** |

1차 부대서류 패키지에 등록된 10종이 모두 LIVE 상태로 전환 완료되었다.  
핵심서류 90종(form_registry)과 document_catalog.yml은 일절 변경하지 않았다.

---

## 2. 핵심서류 v1.0와 부대서류의 분리 원칙

```
핵심서류 (90종)                    부대서류 (10종)
─────────────────────             ─────────────────────────────
document_catalog.yml              supplementary_registry.py
form_registry.py                  (독립 운영)
  └─ 87개 FormSpec 등록            └─ 10개 SupplementalSpec 등록

독립 document_id 부여              부모 form_type에 연결
법정서류 + 실무 핵심서류            파생 출력물 (증빙/첨부)
```

**설계 원칙**:
- 부대서류는 `document_catalog.yml`에 추가하지 않는다.
- 부대서류는 `form_registry.py`에 등록하지 않는다.
- 부대서류는 `supplementary_registry.py`를 통해서만 관리한다.
- 핵심서류 작성 시 파생 생성되는 첨부·보조 출력물 전용이다.

---

## 3. supplementary_registry 구조

```python
# engine/output/supplementary_registry.py

@dataclass(frozen=True)
class SupplementalSpec:
    supplemental_type: str          # 고유 식별자
    display_name: str               # 표시명
    category: str                   # 분류
    parent_form_types: Tuple[...]   # 연동 가능 핵심 form_type
    trigger_condition: str          # 생성 조건
    output_builder: Callable        # builder 함수
    required_fields: Tuple[...]     # 필수 입력 필드
    optional_fields: Tuple[...]     # 선택 입력 필드
    repeat_field: Optional[str]     # 반복 행 필드명
    max_repeat_rows: int            # 반복 행 최대 수
    priority: str                   # P1 / P2 / P3
```

**공개 API**:
```python
list_supplemental_types()                      # 전체 목록
get_supplemental_spec(supplemental_type)       # 단건 조회
get_supplemental_types_for(parent_form_type)   # 핵심서류별 연동 목록
build_supplemental_excel(supplemental_type, form_data)  # xlsx 생성
```

---

## 4. LIVE 10종 목록

| # | supplemental_type | 표시명 | 분류 | max_rows | 우선순위 |
|---|-------------------|--------|------|----------|----------|
| 1 | `attendance_roster` | 참석자 명부 | common | 40 | P1 |
| 2 | `photo_attachment_sheet` | 사진대지 | common | 12 | P1 |
| 3 | `document_attachment_list` | 첨부서류 목록표 | common | 20 | P1 |
| 4 | `confined_space_gas_measurement` | 산소·가스농도 측정기록표 | ptw | 20 | P1 |
| 5 | `work_completion_confirmation` | 작업 종료 확인서 | ptw | — | P1 |
| 6 | `improvement_completion_check` | 개선조치 완료 확인서 | ra_tbm | 15 | P1 |
| 7 | `equipment_operator_qualification_check` | 운전원 자격 확인표 | equipment | 10 | P1 |
| 8 | `watchman_assignment_confirmation` | 감시인 배치 확인서 | ptw | — | P2 |
| 9 | `education_makeup_confirmation` | 미참석자 추가교육 확인서 | education | 20 | P2 |
| 10 | `ppe_receipt_confirmation` | 보호구 수령 확인서 | equipment | 20 | P2 |

---

## 5. 각 부대서류 용도 및 연결 핵심서류

### 5-1. attendance_roster — 참석자 명부
**용도**: 교육, 회의, TBM, 작업허가, 위험성평가 등 핵심서류 작성 시 참석자를 목록화하는 공통 부대서류.  
**연결**: education_log, special_education_log, risk_assessment_meeting_minutes, tbm_log, safety_committee_minutes, confined_space_permit 외 11종  
**builder**: `engine/output/attendance_roster_builder.py`

### 5-2. photo_attachment_sheet — 사진대지
**용도**: 교육, 사고, 개선 등 핵심서류에 첨부하는 사진 목록·배치 표.  
**연결**: education_log, special_education_log, industrial_accident_report, near_miss_report, accident_root_cause_prevention_report 외 3종  
**builder**: `engine/output/photo_attachment_sheet_builder.py`

### 5-3. document_attachment_list — 첨부서류 목록표
**용도**: 제출 패키지 구성 시 첨부서류 2건 이상을 목록화하는 부대서류.  
**연결**: equipment_entry_application, equipment_insurance_inspection_check, industrial_accident_report, serious_accident_immediate_report, contractor_safety_document_checklist  
**builder**: `engine/output/document_attachment_list_builder.py`

### 5-4. confined_space_gas_measurement — 산소·가스농도 측정기록표
**용도**: 밀폐공간 작업 전·중·후 산소 및 유해가스(H₂S, CO, LEL, CO₂) 농도 측정 결과 기록.  
**연결**: confined_space_permit, confined_space_checklist, confined_space_workplan  
**builder**: `engine/output/confined_space_gas_measurement_builder.py`

### 5-5. work_completion_confirmation — 작업 종료 확인서
**용도**: PTW 작업 종료 후 잔류위험·정리정돈·격리해제·장비회수·출입자 철수 확인.  
**연결**: confined_space_permit, hot_work_permit, work_at_height_permit 외 5종  
**builder**: `engine/output/work_completion_confirmation_builder.py`

### 5-6. improvement_completion_check — 개선조치 완료 확인서
**용도**: 위험성평가 개선대책·부적합 조치·재발방지대책 이행 완료 확인.  
**연결**: risk_assessment, risk_assessment_register, near_miss_report, accident_root_cause_prevention_report  
**builder**: `engine/output/improvement_completion_check_builder.py`

### 5-7. equipment_operator_qualification_check — 운전원 자격 확인표
**용도**: 건설기계·크레인·고소작업대·지게차 등 운전원 면허·자격·교육·경력 확인.  
**연결**: equipment_entry_application, tower_crane_workplan, mobile_crane_workplan 외 5종  
**builder**: `engine/output/equipment_operator_qualification_check_builder.py`

### 5-8. watchman_assignment_confirmation — 감시인 배치 확인서
**용도**: 밀폐공간·화기작업·방사선 등 고위험 작업의 감시인·화재감시자·출입통제자 배치 및 작업중지 권한 확인.  
**연결**: confined_space_permit, hot_work_permit, radiography_work_permit  
**builder**: `engine/output/watchman_assignment_confirmation_builder.py`

### 5-9. education_makeup_confirmation — 미참석자 추가교육 확인서
**용도**: 안전보건교육 미참석자·추가교육 대상자에 대한 보완교육 실시 확인.  
**연결**: education_log, special_education_log  
**builder**: `engine/output/education_makeup_confirmation_builder.py`

### 5-10. ppe_receipt_confirmation — 보호구 수령 확인서
**용도**: 안전모·안전화·안전대·마스크 등 개인보호구 지급 및 착용·관리방법 설명 수령 확인.  
**연결**: ppe_issue_register, ppe_management_checklist  
**builder**: `engine/output/ppe_receipt_confirmation_builder.py`

---

## 6. main catalog / form_registry 변경 없음 확인

```
document_catalog.yml   변경 없음 — 부대서류 10종 미등록 (설계 원칙 준수)
form_registry.py       변경 없음 — FormSpec 87건 유지
```

부대서류는 `supplementary_registry.py` 전용 관리 원칙을 엄격히 준수하였다.

---

## 7. audit 결과

```
전체: 87종  |  PASS: 33  |  WARN: 54  |  FAIL: 0
최종 판정: PASS
```

WARN 54건은 기존부터 존재하던 섹션 수 부족·인쇄 설정 없음 등 경고이며,  
이번 부대서류 작업에서 기존 87종을 수정하지 않아 WARN 건수 변동 없음.  
FAIL 0건 유지.

---

## 8. smoke 테스트 결과

| supplemental_type | 입력 조건 | 결과 |
|-------------------|-----------|------|
| `attendance_roster` | blank (필수 필드만) | 7,513 bytes OK |
| `photo_attachment_sheet` | blank (필수 필드만) | 7,820 bytes OK |
| `ppe_receipt_confirmation` | blank (필수 필드만) | 8,272 bytes OK |

blank 입력(필수 필드만)에서도 xlsx 파일이 정상 생성되며, 공란 행이 포함된 양식 출력이 확인되었다.

---

## 9. 구현 이력 (커밋 순서)

| 커밋 | 부대서류 | builder 파일 |
|------|----------|-------------|
| `5f37ff3` | confined_space_gas_measurement | confined_space_gas_measurement_builder.py |
| `0c78d4e` | work_completion_confirmation | work_completion_confirmation_builder.py |
| `4a061f4` | improvement_completion_check | improvement_completion_check_builder.py |
| `0d2906a` | equipment_operator_qualification_check | equipment_operator_qualification_check_builder.py |
| `39a7807` | watchman_assignment_confirmation | watchman_assignment_confirmation_builder.py |
| `74f58db` | education_makeup_confirmation | education_makeup_confirmation_builder.py |
| `750ffbd` | ppe_receipt_confirmation | ppe_receipt_confirmation_builder.py |

※ attendance_roster, photo_attachment_sheet, document_attachment_list 3종은 이전 패키지에서 구현 완료.

---

## 10. 다음 단계 제안

### 2차 부대서류 패키지 후보
- **외국인 근로자 다국어 보호구 확인서**: ppe_receipt_confirmation의 다국어 확장판 (한/영/중/베트남어)
- **위험성평가 결과 공지문**: 평가 결과를 근로자에게 공지하는 1페이지 요약 서식
- **안전시설 점검 사진일지**: 안전시설(추락방호망, 안전난간 등) 설치 및 점검 사진 기록
- **일일 안전점검 체크리스트**: 작업 전 일일 안전상태 점검 기록

### 웹 연동 기능 개발
- **핵심서류 + 부대서류 자동 패키지 생성**: 핵심서류 작성 시 연동 부대서류 선택 UI
- **문서 패키지 ZIP 출력**: 핵심서류 + 선택 부대서류를 ZIP으로 일괄 다운로드
- **프로젝트별 문서 보관함**: 생성된 서류를 프로젝트/날짜/종류별로 보관·조회

### 품질 개선
- **인쇄 설정 추가**: A4 가로/세로 fitToPage, 여백 설정 (현재 WARN 원인)
- **섹션 수 보완**: 핵심서류 WARN 54건 중 섹션 수 부족 51건 개선
