# data/masters/safety/equipment/

장비 유형 마스터 데이터.

## 목적
현장에서 사용되는 장비의 유형 분류(16종)와 개별 장비(31종) 코드를 관리한다.
`sp_equipment_types` 테이블의 정적 파일 원본이다.
Knowledge DB의 `equipment` 테이블 및 `data/risk_db/equipment/equipment_master.json`과 연계된다.

## 저장할 파일 종류
- `equipment_types.yml` — 장비 유형 분류 (16종 type_code + 31종 장비 목록)

## 데이터 검증 기준
- `type_code` 중복 없어야 함
- `equipment_code` 중복 없어야 함
- `equipment_code`는 Knowledge DB `equipment.equipment_code`와 일치해야 함
- `law_ref`가 있는 항목은 조항 번호까지 명시

## 법정/실무 구분 방식
- `source_type: law` — 산안규칙 조항에 명시된 장비 (점검/사용 의무 규정 있음)
- `source_type: practical` — 현장 관행 장비 (법령 직접 근거 없음)
- `source_type: NEEDS_VERIFICATION` — 근거 미확인

## 원본 파일
`data/risk_db/equipment/equipment_master.json` (31종, 2026-04-20 기준)

## TODO
- [ ] 16종 유형 분류와 31종 장비 코드 매핑 완성
- [ ] 장비별 자체검사 대상 여부 표시 (산안법 제93조)
- [ ] 장비별 작동 전 점검 항목 연결
