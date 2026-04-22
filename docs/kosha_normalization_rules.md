# KOSHA 문서 정규화 규칙 v1.0

## 1. 제목 정규화 규칙

### 1-1. 접두어 제거 패턴
| 원본 패턴 | 처리 |
|-----------|------|
| `[중대재해_건설업]` | 제거 (대괄호 포함) |
| `[중대재해_제조업]` | 제거 |
| `(KOSHA GUIDE)` | 제거 |
| `◆`, `▶`, `■` 등 특수문자 선두 | 제거 |
| `제00호`, `개정 0000.00.00` 등 문서번호 | 제거 |

### 1-2. 정규화 순서
1. 양쪽 공백 제거 (`strip()`)
2. 대괄호 접두어 제거 (`re.sub(r'^\[.+?\]\s*', '')`)
3. 소괄호 문서번호 제거 (`re.sub(r'\(KOSHA.+?\)', '')`)
4. 연속 공백 단일화 (`re.sub(r'\s+', ' ')`)
5. 결과 `strip()`

### 1-3. 언어 판정
- 한글 비율 50% 이상 → `language: ko`
- 영문 비율 50% 이상 → `language: en`
- 그 외 → `language: unknown`

---

## 2. 본문 정리 규칙

### 2-1. 텍스트 추출 우선순위
1. PyMuPDF (`fitz`) — 속도 우선
2. pdfminer — PyMuPDF 실패 시 fallback

### 2-2. 본문 정제 처리
| 처리 항목 | 규칙 |
|-----------|------|
| 헤더/푸터 반복 텍스트 | 3회 이상 동일 줄 → 제거 |
| 연속 빈 줄 | 2줄 이상 → 1줄로 축약 |
| 페이지 번호 | `^\d+$` 단독 줄 → 제거 |
| 특수문자 줄 | `^[─━═\-=]{5,}$` → 제거 |
| 최대 저장 길이 | 8,000자 (JSON `content` 필드) |
| 정규화 후 저장 필드 | `body_text` (스키마 기준) |

---

## 3. 중복 판정 기준

### 3-1. 1차 중복 (수집 단계)
- `source_id` (`medSeq` 등 원천 ID) 기준
- `_seen` Set에 등록 → 동일 ID 재수집 skip

### 3-2. 2차 중복 (파일 단계)
- `file_sha256` (PDF 원본 SHA-256) 기준
- 동일 해시 파일 존재 시 PDF 재저장 skip
- JSON은 갱신 (`collected_at` 업데이트)

### 3-3. 3차 중복 (매핑 단계)
- `title_normalized` + `published_at` 조합
- 동일 제목+날짜 → 최신 수집 기준 유지, 이전 버전 `status: excluded`

---

## 4. has_text 판정 기준

| 조건 | has_text |
|------|----------|
| 추출 텍스트 500자 이상 | `true` |
| 추출 텍스트 500자 미만 | `false` |
| PDF 파싱 실패 | `false` |
| PDF 아닌 파일 형식 | `false` |
| 다운로드 실패/timeout | `false` |

`has_text: false` 문서는 매핑 대상에서 제외하고 `status: raw`로 보관.  
향후 OCR 파이프라인 연계 시 `status: ocr_pending`으로 전환 가능.

---

## 5. 짧은 문서 처리 기준

| 조건 | 처리 |
|------|------|
| `content_length` 0 | 이미지PDF 또는 다운로드 실패. `has_text: false` |
| `content_length` 1~499 | 텍스트 레이어 있으나 내용 부족. `has_text: false`, 내용 보존 |
| `content_length` 500~2000 | 짧은 OPL 문서. `has_text: true`, 매핑 시 신뢰도 0.6 적용 |
| `content_length` 2001 이상 | 정상 문서. `has_text: true`, 매핑 신뢰도 1.0 |

---

## 6. law / kosha / expc 공통 확장 방안

### 6-1. 공통 스키마 적용
`kosha_document_schema.json` 기준으로 모든 소스 통일:
- `source`: `kosha` | `law` | `expc` | `admrul`
- `doc_category`: 소스별 고유 코드 (`kosha_opl`, `law_statute` 등)
- `work_types`, `hazards`, `equipment`: 동일 매핑 사전 공유

### 6-2. 소스별 필드 매핑 대응표

| 필드 | kosha | law_statute | law_expc |
|------|-------|-------------|----------|
| `source_id` | `medSeq` | `MST` | `expc_id` |
| `title` | `medName` | `법령명` | `질의제목` |
| `body_text` | PDF 추출 | 조문 텍스트 | 질의+회답+이유 |
| `published_at` | `contsRegYmd` | `시행일자` | `회신일자` |
| `industry` | KOSHA 업종 분류 | 적용 대상 업종 | 적용 업종 |

### 6-3. 매핑 파이프라인 설계 원칙
1. **수집 단계** (`status: raw`): 원본 그대로 JSON 저장
2. **정규화 단계** (`status: normalized`): 제목·본문 정제, 스키마 변환
3. **매핑 단계** (`status: mapped`): 키워드 기반 `work_types` / `hazards` / `equipment` 태깅
4. **제외 단계** (`status: excluded`): 이미지PDF, 외국어, 중복 문서

### 6-4. 향후 AI 매핑 연계 지점
- `hazard_keywords.json`, `work_type_keywords.json` → 1차 룰베이스 매핑
- 룰베이스 미분류 문서 → Claude API (`claude-sonnet-4-6`) 보조 매핑
- 신뢰도 0.7 미만 → `tags`에 `needs_review` 추가
