# 위험성평가 매핑 엔진 — 공통 규칙 문서

버전: 1.1  
기준일: 2026-04-23  
기반 검증: 고소작업 4 hazard PASS (migration 0009)

---

## 1. 테이블 구조 (risk_mapping_core)

| 컬럼 | 타입 | 규칙 |
|------|------|------|
| work_type | TEXT NOT NULL | 작업명 (예: "고소작업") |
| hazard | TEXT NOT NULL | 위험요인 (예: "추락") |
| related_law_ids | JSONB | documents.id 배열 — source_type='law' |
| related_moel_expc_ids | JSONB | documents.id 배열 — source_type='moel_expc' |
| related_kosha_ids | JSONB | documents.id 배열 — source_type='kosha' 또는 'kosha_form' |
| control_measures | JSONB | `{"source": "...", "measures": [...]}` 구조 |
| confidence_score | NUMERIC(3,2) | 0.00~1.00 — confidence_scoring_rule.md 규칙 적용 |
| evidence_summary | TEXT | 300~800자 요약문 |
| created_at | TIMESTAMPTZ | 자동 생성 |

### UNIQUE 제약
```sql
UNIQUE (work_type, hazard)
```

---

## 2. source_type 명칭 규칙

DB `documents.source_type` 실제 값:

| source_type | 의미 | 매핑 컬럼 |
|-------------|------|---------|
| `law` | 법령 조문 | `related_law_ids` |
| `moel_expc` | 고용노동부 법령해석례 | `related_moel_expc_ids` |
| `kosha` | KOSHA 지식DB 자료 | `related_kosha_ids` |
| `expc` | 기타 해석례 (별도 수집) | 매핑 대상 아님 (이번 엔진 범위 외) |

**주의:** `expc` ≠ `moel_expc`. 이 엔진은 `moel_expc`만 사용한다.

---

## 3. control_measures 저장 형식

```json
{
  "source": "law+kosha",
  "measures": [
    "안전난간 설치 (산안기준규칙 제13조)",
    "안전대 착용",
    "작업발판 설치",
    "추락 위험구역 출입통제",
    "작업계획서 작성"
  ]
}
```

- `source` 값: `"law"` / `"kosha"` / `"law+kosha"` / `"manual"`
- `measures` 배열: 4~6개, 실행형 동사 사용
- 조회 경로: `control_measures->'measures'`
- 길이 제한: 단일 문장 50자 이내 권장

---

## 4. hazard 정규화 규칙

| 표준 명칭 | 사용 작업 | 정의 |
|----------|---------|------|
| 추락 | 고소작업, 전기작업, 이동식비계 작업, 고소작업대 작업, 배관/설비 설치 작업 | 사람이 높은 곳에서 떨어지는 위험 |
| 낙하물 | 고소작업, 이동식비계 작업, 배관/설비 설치 작업 | 물체·자재가 위에서 아래로 떨어지는 위험 |
| 낙하 | 양중작업 | 인양 중인 화물·중량물이 추락하는 위험 |
| 전도 | 고소작업, 굴착작업, 양중작업, 이동식비계 작업, 고소작업대 작업 | 장비·작업대·비계가 넘어지는 위험 |
| 협착 | 고소작업, 전기작업, 굴착작업, 양중작업, 고소작업대 작업, 배관/설비 설치 작업 | 사람이 장비·구조물 사이에 끼이는 위험 |
| 충돌 | 양중작업, 고소작업대 작업 | 이동하는 장비·인양물과 사람이 부딪히는 위험 |
| 붕괴 | 굴착작업, 이동식비계 작업 | 지반·구조물·비계가 무너지는 위험 |
| 매몰 | 굴착작업 | 지반이 무너져 사람이 묻히는 위험 |
| 감전 | 전기작업 | 충전 전류가 인체를 통과하는 위험 |
| 아크·화재 | 전기작업 | 아크 방전으로 인한 화재·플래시 위험 |
| 화재 | 용접작업, 배관/설비 설치 작업 | 인화성 물질 점화로 인한 화재 |
| 폭발 | 용접작업 | 가연성 가스·증기의 폭발 위험 |
| 화상 | 용접작업 | 고온 불꽃·슬래그·자외선에 의한 화상 |
| 흄·가스 | 용접작업 | 용접 흄·유해가스 흡입 건강 위험 |
| 질식 | 밀폐공간 작업 | 산소 결핍으로 인한 의식 상실·사망 |
| 중독 | 밀폐공간 작업 | 유해가스 흡입으로 인한 중독 |
| 화재·폭발 | 밀폐공간 작업 | 밀폐 공간 내 가연성 가스 축적으로 인한 위험 |
| 구조지연 | 밀폐공간 작업 | 사고 발생 시 구조 지연으로 인한 피해 악화 |
| 비산 | 절단/천공 작업 | 절단·연삭 파편이 사방으로 튀는 위험 |
| 절단상 | 절단/천공 작업 | 날카로운 날에 신체가 절단되는 위험 |
| 분진 | 절단/천공 작업 | 절단·천공 시 발생하는 분진 흡입 건강 위험 |
| 소음 | 절단/천공 작업 | 고강도 소음에 의한 청력 손상 |

---

## 5. 보호 규칙 (고소작업 row)

- 고소작업 4 row (id=1~4)는 0009 migration 기준 PASS row.
- 이후 migration에서 **UPDATE 금지** (evidence_summary 포함).
- 변경 필요 시 반드시 diff 보고서 생성 후 수동 검토.
- 0010 migration에서 evidence_summary UPDATE가 발생한 점은 기록상 위반으로 문서화.

---

## 6. 참조 우선순위

```
1순위: 작업명 + hazard 동시 본문 명시 문서
2순위: hazard 직접 명시 + 조치 연결 문서
3순위: hazard 단독 명시 문서
4순위: 일반론 문서 (보완용)
```

---

## 7. 불변 규칙

- documents 테이블 수정 금지 (read-only)
- risk_mapping_core 기존 고소작업 row 무단 UPDATE 금지
- confidence_score 임의 부여 금지 → confidence_scoring_rule.md 준수
- source_type 명칭: law / moel_expc / kosha 만 사용
