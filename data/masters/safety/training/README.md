# data/masters/safety/training/

교육 유형 마스터 데이터.

## 목적
산업안전보건법에 따른 교육 유형(정기, 채용시, 특별, TBM 등)의 코드, 시간, 주기, 법령 근거를 관리한다.
`sp_training_types` 테이블의 정적 파일 원본이다.

## 저장할 파일 종류
- `training_types.yml` — 교육 유형 마스터 (training_code, 명칭, 시간, 주기, 법령)

## 데이터 검증 기준
- `training_code` 중복 없어야 함
- `required_hours`는 법령에 명시된 경우만 수록 (불확실하면 null)
- `cycle` 필드는 법령 원문 표현 그대로 기재
- 법령 근거 없는 항목: `verification_status: NEEDS_VERIFICATION`

## 법정/실무 구분 방식
- `source_type: law` — 산안법/시행규칙에 시간·주기 명시
- `source_type: kosha` — KOSHA GUIDE 권고 교육
- `source_type: practical` — 현장 관행 (TBM 등)
- `source_type: NEEDS_VERIFICATION` — 근거 미확인

## 주요 교육 카테고리
- `regular`: 정기안전보건교육 (매반기/매분기)
- `onboarding`: 채용시 교육
- `task_change`: 작업변경시 교육
- `special`: 특별안전보건교육 (16시간 등)
- `tbm`: TBM (Tool Box Meeting)
- `msds`: 물질안전보건자료(MSDS) 교육
- `confined_space`: 밀폐공간 특별교육

## TODO
- [ ] 근로자 교육과 관리자 교육 구분 필드 추가
- [ ] 교육 유형별 이수증 발급 여부 표시
- [ ] 온라인/집합 교육 구분 필드 검토
