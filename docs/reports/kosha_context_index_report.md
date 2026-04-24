# KOSHA Context Index 품질 리포트

생성일시: 2026-04-25 00:22 KST  |  분류기버전: v1.0

## 요약

| 항목 | 수치 |
|------|------|
| 분류 source (classifications) | 2,047건 |
| indexed total rows | 4,797 |
| indexed materials (distinct) | 1,928 |
| indexed chunks (distinct) | 4,755 |
| fallback 행 (chunk 없는 자료) | 42 |
| 건설업 indexed | 1,028 |
| 위험요인 태그 있는 행 | 3,971 |
| 작업유형 태그 있는 행 | 3,433 |
| 장비 태그 있는 행 | 1,411 |
| UNKNOWN 행 (태그 전무) | 686 |
| context_score null | 0 |
| search_text null | 0 |

## 업종별 분포

| 업종 | 행 수 |
|------|-------|
| other | 2,246 |
| construction | 1,028 |
| manufacturing | 822 |
| service | 694 |
| shipbuilding | 7 |

## Context Score 분포

| 구간 | 행 수 |
|------|-------|
| <0.25 | 757 |
| 0.75+ | 104 |
| 0.50-0.74 | 1,844 |
| 0.25-0.49 | 2,092 |

## 검색 검증 결과

| 케이스 | 결과 건수 | 판정 |
|--------|-----------|------|
| 건설업+추락 | 10 | OK |
| 건설업+굴착 | 10 | OK |
| 굴착기+협착 | 10 | OK |
| 이동식크레인+양중 | 10 | OK |
| 밀폐공간+질식 | 10 | OK |
| 용접+화재폭발 | 10 | OK |
| 전기+감전 | 10 | OK |
| 작업환경측정 | 10 | OK |
| 특수건강진단 | 10 | OK |
| MSDS/화학물질 | 10 | OK |

## Backlog

| 유형 | 건수 | 집계 SQL |
|------|------|---------|
| image_pdf | 2,434 | `WHERE parse_status='image_pdf'` |
| failed_unzip | 111 | `WHERE parse_status='failed_unzip'` |
| hwp pending | 9 | `WHERE parse_status='pending' AND file_type='hwp'` |
| text_pdf failed | 64 | `WHERE parse_status='failed' AND file_type='pdf'` |

## 다음 단계

- [ ] 위험성평가 생성 엔진에서 `kosha_context_index` read-only 연결
- [ ] context_score 임계값(≥0.50) 기준 엔진 필터링 설계
- [ ] 0건 검색 케이스 보강: 키워드 사전 확장 또는 FTS 보완
- [ ] image_pdf 2,434건 OCR 후 분류·인덱싱 확장