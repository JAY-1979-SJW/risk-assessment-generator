# data/masters/safety/inspection/

점검 유형 마스터 데이터.

## 목적
산업안전보건법 및 산업안전보건기준에 관한 규칙에 따른 점검 유형(일상점검, 정기점검, 자체검사 등)의 코드, 대상, 주기, 법령 근거를 관리한다.
`sp_inspection_types` 테이블의 정적 파일 원본이다.

## 저장할 파일 종류
- `inspection_types.yml` — 점검 유형 마스터 (inspection_code, 명칭, 대상, 주기, 법령)

## 데이터 검증 기준
- `inspection_code` 중복 없어야 함
- `cycle` 필드는 법령 원문 또는 KOSHA GUIDE 표현 그대로 기재
- `target_type`은 equipment | workplace | process | chemical 중 하나
- 법령 근거 없는 항목: `verification_status: NEEDS_VERIFICATION`

## 법정/실무 구분 방식
- `source_type: law` — 법령 조항에 점검 주기/방법 명시
- `source_type: kosha` — KOSHA GUIDE 권고 점검 절차
- `source_type: practical` — 현장 관행 점검
- `source_type: NEEDS_VERIFICATION` — 근거 미확인

## 주요 점검 유형
- 작업 전 일상점검 (산안규칙 각 장비 조항)
- 월 1회 정기점검 (타워크레인 등)
- 자체검사 (산안법 제93조 대상 기계/기구)
- 특별점검 (사고 후, 장기 미사용 후 재가동 전)
- 밀폐공간 작업 전 산소/유해가스 측정

## TODO
- [ ] 자체검사 대상 기계/기구 목록 연결 (산안법 제93조 별표)
- [ ] 점검표 양식(CL 시리즈) 연결
- [ ] 점검 결과 이상 발견 시 조치 절차 연결
