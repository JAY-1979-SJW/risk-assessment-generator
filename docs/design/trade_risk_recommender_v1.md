# 공종별 위험성평가 추천 엔진 v1

작성일: 2026-04-25  
버전: 1.0  
모듈: `engine/recommendation/trade_risk_recommender.py`

---

## 1. 목적

`trade_id`를 입력하면 위험성평가표 작성에 필요한 요소를 표준 payload로 반환.  
RA-001 builder 구현 전 단계로, payload 구조를 안정화해 향후 연결점을 고정.

---

## 2. 입력값

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|------|------|
| trade_id | str | ✅ | 공종 ID (예: `FIRE_PIPE_INSTALL`) |
| site_context | dict \| None | ❌ | 현장 정보 (위험도 계산 미사용) |
| selected_common_work_ids | list[str] | ❌ | merge할 공통 고위험작업 ID 목록 |

`site_context` 허용 필드:

```python
{
  "site_name": str | None,
  "work_location": str | None,
  "work_date": str | None,        # YYYY-MM-DD
  "workers_count": int | None,
  "equipment_used": list[str],
}
```

---

## 3. 출력 payload 구조

```json
{
  "trade_id": "FIRE_PIPE_INSTALL",
  "trade_name": "소방 배관 설치",
  "trade_group": "소방설비",
  "site_context": {
    "site_name": null,
    "work_location": null,
    "work_date": null,
    "workers_count": null,
    "equipment_used": []
  },
  "risk_items": [
    {
      "hazard_id": "FALL_FROM_HEIGHT",
      "hazard_name": "추락",
      "category": "신체적 위험",
      "risk_scenario": "소방 배관 설치 작업 중 추락 발생 가능",
      "typical_causes": ["..."],
      "typical_consequences": ["..."],
      "controls": [
        {
          "control_id": "CTRL_FALL_01",
          "control_type": "ENGINEERING",
          "priority": 1,
          "description": "안전난간 설치 ...",
          "applicable_conditions": "..."
        }
      ],
      "related_documents": ["PTW-003", "CL-001"],
      "source_trade_ids": ["FIRE_PIPE_INSTALL"],
      "source_status": "PRACTICAL"
    }
  ],
  "required_documents": ["RA-001", "RA-004", "ED-003"],
  "recommended_documents": ["PTW-002", "PTW-003", "CL-003"],
  "required_trainings": ["EDU_SPECIAL_16H", "EDU_CONSTRUCTION_BASIC", "EDU_TBM"],
  "required_permits": ["PTW-002", "PTW-003"],
  "common_equipment": ["welding_machine", "chain_block"],
  "ppe": ["safety_helmet", "safety_harness"],
  "warnings": [],
  "source_trace": ["FIRE_PIPE_INSTALL"],
  "source_status_summary": {
    "VERIFIED": 0,
    "PARTIAL_VERIFIED": 0,
    "NEEDS_VERIFICATION": 0,
    "PRACTICAL": 7
  }
}
```

---

## 4. 공종 단독 추천 예시

```python
from engine.recommendation.trade_risk_recommender import build_trade_risk_recommendation

payload = build_trade_risk_recommendation(
    trade_id="ELEC_CABLE_TRAY",
    site_context={"site_name": "강남 현장", "work_location": "지하1층"},
)
print(payload["risk_items"])   # 위험요인 리스트
print(payload["required_documents"])  # ['RA-001', 'RA-004', 'ED-003']
print(payload["required_permits"])    # ['PTW-003', 'PTW-004']
```

CLI:

```bash
python scripts/dry_run_trade_risk_recommendation.py \
  --trade-id ELEC_CABLE_TRAY \
  --site-name "강남 현장" \
  --work-location "지하1층"
```

---

## 5. 공종 + 공통 고위험작업 merge 예시

```python
from engine.recommendation.trade_risk_recommender import (
    get_trade_preset,
    merge_common_high_risk_presets,
)

base = get_trade_preset("FIRE_PIPE_INSTALL")
merged = merge_common_high_risk_presets(
    base,
    selected_common_work_ids=["COMMON_HOT_WORK", "COMMON_WORK_AT_HEIGHT"],
)
print(merged["source_trace"])
# ['FIRE_PIPE_INSTALL', 'COMMON_HOT_WORK', 'COMMON_WORK_AT_HEIGHT']
print(len(merged["risk_items"]))  # 중복 제거된 총 위험요인 수
```

CLI:

```bash
python scripts/dry_run_trade_risk_recommendation.py \
  --trade-id FIRE_PIPE_INSTALL \
  --common-work COMMON_HOT_WORK \
  --common-work COMMON_WORK_AT_HEIGHT
```

---

## 6. source_status 의미

| 값 | 의미 |
|----|------|
| `VERIFIED` | 법령 원문 직접 확인 완료 |
| `PARTIAL_VERIFIED` | 일부 조항 확인, 전체 미검증 |
| `PRACTICAL` | 실무 경험 기반, 법령 직접 확인 없음 |
| `NEEDS_VERIFICATION` | skeleton 또는 미확인 — 사용 전 검토 필요 |

`source_status_summary`는 risk_items 전체의 검증 수준을 집계.  
PRACTICAL/NEEDS_VERIFICATION 비율이 높으면 RA-001 출력 전 수동 검토 권장.

---

## 7. RA-001 builder 연결 예정 방식

현재 RA-001 builder 미구현. 구현 시 아래 방식으로 payload를 입력:

```python
# 예정 (미구현)
from engine.recommendation.trade_risk_recommender import build_trade_risk_recommendation
from engine.output.risk_assessment_builder import build_ra001_excel

payload = build_trade_risk_recommendation("FIRE_PIPE_INSTALL")
excel_bytes = build_ra001_excel(payload)
```

payload의 `risk_items` 각 항목이 RA-001 행 하나에 대응:

| payload 필드 | RA-001 열 |
|-------------|-----------|
| `hazard_name` + `risk_scenario` | 위험요인 및 위험성 |
| `controls[].description` | 현재 안전조치 / 추가 안전조치 |
| `required_documents` | 관련 서류 |
| `required_permits` | 작업허가서 |

---

## 8. UI 연결 예정 방식

1. 사용자: 공종 선택 (드롭다운)
2. API: `GET /api/v1/recommend/{trade_id}` → payload 반환
3. UI: 위험요인·감소대책·서류 미리보기 표시
4. 사용자: 항목 선택/해제 후 RA-001 Excel 생성 요청

---

## 9. 현재 한계

| 항목 | 상태 |
|------|------|
| 위험성 등급 산정 | 미구현 (빈도×강도 매트릭스 연동 필요) |
| site_context 활용 | 미구현 (metadata만 포함, 위험도 미반영) |
| skeleton 공종 추천 | 미지원 (NEEDS_VERIFICATION 상태) |
| conditional_permits 반영 | 미구현 (조건부 허가서는 merge 미포함) |
| 공종 자동 분류 | 미구현 (trade_id 직접 입력 필요) |
| RA-001 builder 연결 | 미구현 |

---

## 10. 다음 단계 후보

1. **RA-001 위험성평가표 builder** 구현 — 이 payload를 입력으로 활용
2. **위험성 등급 매트릭스 연동** — 빈도(F) × 강도(S) → 위험성(R) 자동 계산
3. **conditional_permits 반영** — site_context 기반 조건부 허가서 자동 추가
4. **skeleton 공종 상세화** — 건축/토목/철골/해체 NEEDS_VERIFICATION → PARTIAL_VERIFIED 전환
5. **API 엔드포인트 추가** — `/api/v1/recommend/{trade_id}`
