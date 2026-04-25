# data/masters/safety/documents/

안전서류 카탈로그 마스터 데이터.

## 목적
안전서류 90종(목표)의 식별자, 명칭, 법령 근거, 의무 유형, 구현 상태를 관리한다.
`sp_document_catalog` 테이블의 정적 파일 원본이다.

## 저장할 파일 종류
- `document_catalog.yml` — 전체 서류 카탈로그 (doc_id, 명칭, 분류, 법령, 상태)

## 데이터 검증 기준
- `doc_id` 중복 없어야 함
- `current_status`: DONE | PARTIAL | TODO | EXCLUDED 중 하나
- `priority`: P0 | P1 | P2 | P3 | P4 | EXCLUDED 중 하나
- `form_type`이 있으면 form_registry.py에 등록된 값과 일치해야 함
- 법령 근거 없는 항목: `verification_status: NEEDS_VERIFICATION`

## 법정/실무 구분 방식
- `source_authority: A_OFFICIAL` — 법정 별지/별표 존재
- `source_authority: B_GUIDE` — KOSHA/MOEL 가이드 수준
- `source_authority: GEN_INTERNAL` — 법정 별지 없음, 시스템 자체 생성 표준

## TODO
- [ ] 90종 전체 수록 (현재 23종 → 67종 추가 필요, 법령 검토 후 단계적 등록)
- [ ] form_type 연결 누락 항목 보완
- [ ] autofill_ratio 미계산 항목 계산
