# data/masters/safety/

Safety Platform 마스터 데이터 루트 디렉토리.

## 목적
안전서류 90종, 장비 유형, 교육 유형, 점검 유형, 법령 준거, 매핑 요구사항의 마스터 데이터를 관리한다.
DB 스키마(`safety_platform_core_schema.sql`)의 sp_* 테이블과 1:1 대응하는 정적 파일 저장소다.

## 하위 폴더

| 폴더 | 설명 | DB 대응 테이블 |
|------|------|--------------|
| `documents/` | 안전서류 카탈로그 (90종 목표) | sp_document_catalog |
| `equipment/` | 장비 유형 마스터 | sp_equipment_types |
| `training/` | 교육 유형 마스터 | sp_training_types |
| `inspection/` | 점검 유형 마스터 | sp_inspection_types |
| `compliance/` | 법령/KOSHA 출처 및 조항 | sp_compliance_sources, sp_compliance_clauses |
| `mappings/` | 장비/작업/위험요인별 요구사항 매핑 | sp_*_requirements 테이블군 |

## 데이터 검증 기준
- 모든 YAML 파일은 UTF-8 인코딩
- ID 필드는 파일 내 중복 없어야 함
- 법정 근거 확인 불가 항목은 `verification_status: NEEDS_VERIFICATION` 표시
- 내부 실무 기준은 `source_type: practical` 또는 `source_type: internal` 표시

## 법정/실무 구분 방식
- `law`: 산업안전보건법, 기준규칙 등 법령 조문 직접 근거
- `kosha`: KOSHA GUIDE / 기술지침 (권고 수준)
- `moel`: 고용노동부 고시/해석례
- `practical`: 현장 실무 관행 (법령 근거 없음)
- `internal`: 시스템 내부 기준
- `NEEDS_VERIFICATION`: 근거 미확인 — 검토 필요

## TODO
- [ ] 90종 서류 카탈로그 완성 (현재 23종)
- [ ] 매핑 파일 전체 완성 (현재 대표 예시만 수록)
- [ ] compliance/ 법령 조항 전체 수록
- [ ] DB 적재 스크립트 작성
