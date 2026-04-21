# ra_link_schema 설계 규칙

생성일: 2026-04-21  
단계: 5단계 (worktype/hazard/control/law 4축 통합 연결 설계)

---

## 입력 파일

| 구분 | 경로 |
|---|---|
| work_types | `data/risk_db/work_taxonomy/work_types.json` |
| work_sub_types | `data/risk_db/work_taxonomy/work_sub_types.json` |
| hazards | `data/risk_db/hazard/hazards.json` |
| hazard_controls | `data/risk_db/hazard/hazard_controls.json` |
| work_hazards_map | `data/risk_db/hazard/work_hazards_map.json` |
| law_hazard_map | `data/risk_db/law_mapping/law_hazard_map.json` |
| law_worktype_map | `data/risk_db/law_mapping/law_worktype_map.json` |
| safety_laws_normalized | `data/risk_db/law_normalized/safety_laws_normalized.json` |

---

## 출력 파일

| 파일 | 설명 |
|---|---|
| `data/risk_db/link_design/ra_link_schema.json` | 4축 엔티티·관계 스키마 |
| `data/risk_db/link_design/ra_link_samples.json` | 샘플 연결 데이터 (검증용) |
| `data/risk_db/link_design/ra_link_review_notes.json` | 후속 단계 대비 검토 메모 |

---

## 4축 엔티티 기준 키

| 엔티티 | PK | 출처 |
|---|---|---|
| worktype | work_type_code | work_types.json |
| hazard | hazard_code | hazards.json |
| control | control_code (`{hazard_code}_C{nn:02d}`) | hazard_controls.json 순번 파생 |
| law | law_id (`{category}:{raw_id}`) | safety_laws_normalized.json |

---

## 5가지 관계 축

| 관계 | 방향 | 현황 |
|---|---|---|
| worktype_hazard | work_type → hazard | 48건 (30/132 wt 커버) |
| hazard_control | hazard → control | 90건 (17/17 hz 커버) |
| worktype_law | work_type → law | 268건 (전체) |
| hazard_law | hazard → law | 42건 (전체) |
| control_law | control → law | 설계 전용 5건 샘플 (미완성) |

---

## control_code 파생 규칙

`hazard_controls.json`에 `control_code` 필드 없음 → 파생으로 처리:

```
control_code = f"{hazard_code}_C{순번:02d}"
예: FALL 첫 번째 제어 → FALL_C01
```

순번은 해당 hazard 내 control 항목 순서(0-based + 1).

---

## law_ref → law_id 변환 규칙

`hazard_controls.json`의 `law_ref`는 자유 텍스트:

| 텍스트 패턴 | 변환 결과 |
|---|---|
| "산업안전보건기준에 관한 규칙 제NNN조" | `statute:273603` |
| "산업안전보건법 제NNN조" (기준/규칙 미포함) | `statute:276853` |
| 나머지 | `statute:273603` (기본값) |

---

## 엔진 6단계 흐름

1. 작업유형 입력 (work_type_code)
2. worktype_hazard 조회 → 위험요인 목록
3. hazard_control 조회 → 제어조치 목록
4. worktype_law 조회 → 관련 법령 필터링
5. hazard_law 교차 → 위험요인별 법령 근거
6. control_law 조회 → 제어조치별 조문 근거 제시

---

## review_needed 항목

| 항목 | 심각도 | 내용 |
|---|---|---|
| missing_control_code | HIGH | hazard_controls.json에 control_code 미존재 — 파생 규칙으로 처리 필요 |
| worktype_hazard_partial | MEDIUM | 30/132 work_types만 커버 — 미연결 102개는 6단계 전 보강 필요 |
| hazard_control_partial | MEDIUM | 17/17 hazard 커버되나 일부 hazard 제어조치 수 불균형 |
| law_ref_text_not_id | HIGH | law_ref가 자유 텍스트 — 정규화 후 law_id로 교체 필요 |
| control_law_concentration | LOW | 대다수 control이 statute:273603 1건으로 집중됨 |
| multi_hazard_control | LOW | LOTO(잠금장치) 등 복수 hazard 대응 control 존재 |

---

## 다음 단계

6단계 — `law_control_map` 초안 생성 (전제조건 확인 후 착수)

전제조건:
1. `control_code` 확정 (파생 규칙 또는 hazard_controls.json 컬럼 추가)
2. `hazard_controls.json`의 `law_ref` → `law_id` 정규화
3. `work_hazards_map.json` 커버리지 보강 (선택)
