# data/masters/safety/compliance/

법령/KOSHA 준거 데이터.

## 목적
안전서류/교육/점검의 법적 근거가 되는 법령, 고시, KOSHA GUIDE 출처와 조항 단위 데이터를 관리한다.
`sp_compliance_sources`, `sp_compliance_clauses` 테이블의 정적 파일 원본이다.

## 저장할 파일 종류
- `compliance_sources.yml` — 출처 목록 (법령/고시/KOSHA 각 source_code, 명칭, 유형)
- `compliance_clauses.yml` — 조항 목록 (source_code + article_no + 의무 유형)

## 데이터 검증 기준
- `source_code` 중복 없어야 함
- `article_no`는 "제X조 제X항 제X호" 형식 권장
- `obligation_type`: 작성의무 | 비치의무 | 교육의무 | 점검의무 | 신고의무 중 하나
- 법령 원문 직접 확인 불가 항목: `verification_status: NEEDS_VERIFICATION`
- 법령 원문 확인 완료 항목: `verification_status: confirmed`

## 법정/실무 구분 방식
- `source_type: law` — 산업안전보건법, 산업안전보건기준에 관한 규칙 등 법령
- `source_type: moel` — 고용노동부 고시 (제2023-19호 등)
- `source_type: kosha` — KOSHA GUIDE / 기술지침 (권고 수준)
- `source_type: NEEDS_VERIFICATION` — 출처 원문 미확인

## 주요 법령 출처
- 산업안전보건법 (법률)
- 산업안전보건법 시행령
- 산업안전보건법 시행규칙
- 산업안전보건기준에 관한 규칙
- 고시 제2023-19호 (위험성평가)
- KOSHA GUIDE 시리즈

## TODO
- [ ] 주요 법령 출처 전체 수록
- [ ] 서류 90종 법령 조항 매핑 완성 (현재 주요 항목만)
- [ ] 고시 원문 URL 연결
- [ ] Knowledge DB law_meta와 연계 스크립트 작성
