# KOSHA RAG Risk Engine v1

## 목적

사용자 자유 텍스트 입력 → KOSHA 지식 베이스 검색 → 위험요인/대책/PPE/법적 근거 JSON 반환.
외부 LLM/API 없음. 완전 로컬 deterministic BM25 검색.

---

## 경로

```
engine/rag_risk_engine/
├── schema.py       — 입력/출력 스키마, validate_input()
├── retrieval.py    — BM25Index, tokenize(), normalize_text()
├── assembler.py    — 결과 조합, confidence 산정, warnings 생성
├── engine.py       — run_engine() 오케스트레이터
├── loader.py       — DB / JSON 파일 로더
├── cli.py          — CLI 엔트리포인트
├── tests/
│   ├── test_engine.py
│   └── fixtures/sample_chunks.json
└── samples/        — CLI 검증용 샘플 입력 5종
```

---

## 입력 스키마

| 필드 | 필수 | 타입 | 설명 |
|------|------|------|------|
| `process` | ✓ | str | 공정명 |
| `sub_work` | ✓ | str | 세부작업명 |
| `risk_situation` | ✓ | str | 위험상황 (핵심 입력, 빈 문자열 금지) |
| `risk_category` | — | str\|null | 위험분류 |
| `risk_detail` | — | str\|null | 위험세부분류 |
| `current_measures` | — | str\|null | 현재 안전조치 |
| `legal_basis_hint` | — | str\|null | 법령 검색 힌트 |
| `top_k` | — | int (1~50) | 검색 결과 수 (기본 10) |

### 입력 예시

```json
{
  "process": "건축 골조",
  "sub_work": "시스템 비계 설치",
  "risk_situation": "비계 작업발판 불안정으로 2m 이상 고소에서 추락 위험",
  "risk_category": "작업특성 요인",
  "risk_detail": "추락",
  "top_k": 10
}
```

---

## 출력 스키마

| 필드 | 타입 | 설명 |
|------|------|------|
| `query_summary` | str | 쿼리 요약 (공정/세부작업: 위험상황) |
| `matched_chunks` | list[MatchedChunk] | 검색된 청크 상위 k개 |
| `primary_hazards` | list[str] | 위험 유형 (빈도 순) |
| `recommended_actions` | list[str] | 권고 대책 (태그 청크 우선) |
| `required_ppe` | list[str] | 필요 보호구 |
| `legal_basis_candidates` | list[str] | 법령 근거 후보 |
| `source_chunk_ids` | list[int] | 사용된 청크 ID |
| `confidence` | `low`\|`medium`\|`high` | 검색 품질 |
| `warnings` | list[str] | 데이터 품질 한계 경고 |
| `reasoning_notes` | list[str] | 결과 도출 근거 bullet |

### 출력 예시 (요약)

```json
{
  "query_summary": "건축 골조 / 시스템 비계 설치: 비계 작업발판 불안정으로 추락 위험",
  "primary_hazards": ["추락"],
  "recommended_actions": ["안전난간 설치", "추락방지망 설치", "작업발판 고정"],
  "required_ppe": ["안전모", "안전대"],
  "legal_basis_candidates": ["산업안전보건기준에 관한 규칙 제43조"],
  "source_chunk_ids": [1, 2, 5],
  "confidence": "high",
  "warnings": [],
  "reasoning_notes": [
    "쿼리 요약: ...",
    "상위 청크 BM25+보너스 점수: 9.23",
    "태그 보유 청크 비율: 3/3",
    "감지된 위험 유형: 추락",
    "confidence 판정: high"
  ]
}
```

---

## Retrieval 방식

**BM25** (k1=1.5, b=0.75) — pure Python, 외부 패키지 없음.

### 인덱싱 대상 필드

1. `normalized_text` / `raw_text` (기본 텍스트)
2. `work_type`, `hazard_type`
3. `control_measure`, `ppe`, `law_ref`
4. `keywords` (배열 또는 문자열)

### 토크나이저

- 공백 분리 단어 토큰 (길이 ≥ 2, stopwords 제외)
- 한국어 character bigram 추가 (서브워드 커버리지)

### 쿼리 구성

```
query = risk_situation + sub_work + risk_category + risk_detail + legal_basis_hint
```

`risk_situation`이 앞에 위치하여 IDF 가중치 우선 적용.

---

## Scoring 규칙

| 항목 | 가중치 |
|------|--------|
| BM25 텍스트 점수 | 기본 |
| work_type 매칭 (query 포함) | +2.0 |
| hazard_type 매칭 (query 포함) | +2.5 |
| ppe 필드 존재 | +0.5 |
| law_ref 필드 존재 | +1.0 |
| control_measure 존재 | +0.5 |
| 태그 없음 (work_type & hazard_type null) | -1.0 |
| BM25 점수 = 0 (텍스트 미매칭) | 결과 제외 |
| 노이즈 청크 (텍스트 < 50자) | ×0.2 배율 |

---

## Confidence 규칙

| 조건 | 판정 |
|------|------|
| avg_top3_score ≥ 5.0 AND tag_ratio ≥ 0.6 AND control_measure 존재 | `high` |
| avg_top3_score < 1.5 OR tag_ratio < 0.25 | `low` |
| 그 외 | `medium` |

`tag_ratio`: 상위 k개 청크 중 work_type 또는 hazard_type 있는 비율.

---

## Warnings 규칙

| 조건 | Warning 내용 |
|------|-------------|
| 검색 결과 없음 | 검색 결과 없음: 입력 텍스트와 매칭되는 KOSHA 청크가 없습니다. |
| legal_basis_candidates 빈 배열 | 법령 근거 없음: law_ref가 있는 청크가 검색되지 않았습니다. |
| 태그 없는 청크 > 50% | 태그 미비: 상위 결과 N/M건이 분류 태그 없는 청크입니다. |
| work_type 특정 값 > 70% 편중 | work_type 편향: '설치' 유형이 X%로 과다 비중입니다. |
| confidence == low | 검색 품질 낮음: 쿼리와 강하게 매칭되는 청크가 부족합니다. |

---

## 데이터 한계

- 실제 KOSHA 청크 4,907건 중 태그 없는 청크 31.4% 존재
- law_ref null 비율 높음 → legal_basis_candidates 빈 배열 빈번
- 중복 청크 약 262건 → dedup 로직으로 억제하나 유사 중복은 남을 수 있음
- work_type "설치" 과편향 → bias correction warning으로 보정
- 이미지 PDF 유래 청크(노이즈) 일부 잔존 → 50자 미만 패널티로 억제

---

## CLI 실행법

```bash
# JSON 파일 입력
python -m engine.rag_risk_engine.cli \
  --input engine/rag_risk_engine/samples/sample_fall_scaffold.json \
  --chunks /path/to/chunks.json \
  --pretty

# 인라인 JSON 입력
python -m engine.rag_risk_engine.cli \
  --json '{"process":"건축","sub_work":"비계","risk_situation":"비계 추락 위험"}' \
  --chunks /path/to/chunks.json

# DB 연결 (SSH 터널 필요)
python -m engine.rag_risk_engine.cli \
  --input engine/rag_risk_engine/samples/sample_fall_scaffold.json \
  --use-db --pretty
```

---

## 테스트 실행

```bash
python -m pytest engine/rag_risk_engine/tests/test_engine.py -v
```

| # | 케이스 | 검증 항목 |
|---|--------|-----------|
| 1 | 일반 추락 위험 | primary_hazards 추락, source_chunk_ids 존재 |
| 2 | 고소작업 + 추락 | PPE 안전대, confidence medium+ |
| 3 | 밀폐공간 + 질식 | hazard 질식, PPE 공기호흡기, law_ref 619조 |
| 4 | 감전 | hazard 감전, PPE 절연장갑, actions 전원차단 |
| 5 | 화재/폭발 | hazard 화재/폭발, actions 소화기 |
| 6 | PPE 추출 | required_ppe 비어있지 않음 |
| 7 | 법령 근거 | legal_basis_candidates 산업안전보건 포함 |
| 8 | 태그 없는 청크 fallback | 구조 유지, warnings 정상 동작 |
| 9 | 노이즈 청크 억제 | 극단 노이즈(< 50자) top-3 미포함 |
| 10 | 검색 결과 없음 | confidence low, warnings 없음 메시지 |
| 11 | 필수 입력 누락 | ValueError 발생 |
| 12 | 빈 risk_situation | ValueError 발생 |
| 13 | confidence high 케이스 | medium 또는 high 판정 |
| 14 | confidence low 케이스 | low 또는 medium |
| 15 | JSON 직렬화 | json.dumps 오류 없음 |
| 16 | 중복 청크 억제 | 동일 fp 청크 동시 결과 미포함 |

---

## v1 한계 (명시)

- 정량 점수 산정 없음 (가능성/중대성/위험성 수치 미생성)
- height_m / worker_count / weather 등 구조화 조건 미반영
- 외부 LLM 텍스트 생성 없음 (결과는 검색된 청크 조합)
- 벡터 검색 없음 (의미론적 유사도 미적용)
- law_ref null 다수로 legal_basis_candidates 공백 빈번
- 한국어 형태소 분석 미적용 (bigram 기반 서브워드로 부분 보완)
