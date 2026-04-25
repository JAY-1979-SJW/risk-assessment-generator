# data/masters/safety/mappings/

장비/작업/위험요인별 서류·교육·점검 요구사항 매핑 데이터.

## 목적
"장비 선택 → 필요한 교육 → 필요한 자격 → 필요한 서류 → 필요한 점검" 흐름을 구현하기 위한 N:M 매핑 데이터를 관리한다.
`sp_*_requirements` 테이블군의 정적 파일 원본이다.

## 저장할 파일 종류
- `equipment_document_requirements.yml` — 장비별 필수 서류 (sp_equipment_document_requirements)
- `equipment_training_requirements.yml` — 장비별 필수 교육 (sp_equipment_training_requirements)
- `work_document_requirements.yml` — 작업유형별 필수 서류 (sp_work_document_requirements)
- `work_training_requirements.yml` — 작업유형별 필수 교육 (sp_work_training_requirements)

## 데이터 검증 기준
- 각 파일의 `equipment_code` / `work_type_code`는 Knowledge DB 코드와 일치해야 함
- `doc_id`는 document_catalog.yml의 doc_id와 일치해야 함
- `training_code`는 training_types.yml의 training_code와 일치해야 함
- 법령 직접 근거 있는 항목: `source_type: law`, `verification_status: confirmed`
- 법령 근거 불확실 항목: `verification_status: NEEDS_VERIFICATION`

## 법정/실무 구분 방식
- `source_type: law` — 산안규칙 해당 조항에 명시
- `source_type: kosha` — KOSHA GUIDE 권고
- `source_type: practical` — 현장 관행, 법령 직접 근거 없음
- `source_type: NEEDS_VERIFICATION` — 근거 미확인 — TODO

## 작성 원칙
- 완성하지 않아도 됨. 법령 확인된 항목부터 수록, 나머지는 TODO 표시
- 매핑 1개당 최소 `condition_note` 또는 `legal_basis` 중 하나 필수
- 임의 추론 금지 — 불확실하면 NEEDS_VERIFICATION

## TODO
- [ ] 장비 31종 × 서류 카탈로그 전체 매핑 완성
- [ ] 작업유형 × 서류 카탈로그 전체 매핑 완성
- [ ] 위험요인 × 서류/교육 매핑 파일 추가
- [ ] 점검 요구사항 매핑 파일 추가
