# trade_risk_recommendation → RA-001 위험성평가표 연결 v1

작성일: 2026-04-25  
버전: 1.0  
어댑터: `engine/recommendation/risk_assessment_adapter.py`

---

## 1. 목적

`trade_risk_recommendation` payload를 RA-001 위험성평가표 Excel 입력값으로 변환.  
공종 선택 → 위험요인 추천 → Excel 생성까지 end-to-end 연결을 구현.

---

## 2. 입력 흐름

```
사용자: trade_id 선택
    ↓
trade_risk_recommender.py
    build_trade_risk_recommendation(trade_id)
    또는 merge_common_high_risk_presets(preset, common_ids)
    ↓
risk_assessment_adapter.py
    build_ra001_input_from_trade_recommendation(recommendation)
    ↓
form_excel_builder.py
    render_form_sheet(ws, form_data)   ← 기존 RA-001 Excel 렌더러 재사용
    + 주의사항 시트 추가
    ↓
xlsx bytes
```

---

## 3. trade_risk_recommendation payload 구조 (요약)

```json
{
  "trade_id": "FIRE_PIPE_INSTALL",
  "trade_name": "소방 배관 설치",
  "risk_items": [
    {
      "hazard_id": "FALL_FROM_HEIGHT",
      "hazard_name": "추락",
      "category": "FALL",
      "risk_scenario": "소방 배관 설치 작업 중 추락 발생 가능",
      "controls": [
        {"control_id": "CTRL_FALL_01", "control_type": "ENGINEERING",
         "priority": 1, "description": "안전난간 설치 ..."}
      ]
    }
  ],
  "required_documents": ["RA-001", "RA-004", "ED-003"],
  "required_permits": ["PTW-002", "PTW-003"],
  "required_trainings": ["EDU_SPECIAL_16H", "EDU_CONSTRUCTION_BASIC", "EDU_TBM"]
}
```

---

## 4. RA-001 입력 변환 구조

| payload 필드 | RA-001 셀 (form_excel_builder 키) |
|-------------|----------------------------------|
| `trade_group` | `process` (공정명) |
| `trade_name` + `work_location` | `sub_work` (세부작업명) |
| `hazard.category` (KO 변환) | `hazard_category_major` (위험분류 대) |
| `hazard.hazard_name` | `hazard_category_minor` (위험분류 중) |
| `hazard_name` + `risk_scenario` | `hazard` (유해위험요인) |
| `related_documents` + `required_documents` | `legal_basis` (관련근거) |
| controls priority 1~2 (ENGINEERING/ADMIN) | `current_measures` (현재 안전보건조치) |
| all controls | `control_measures` (위험성 감소대책) |
| v1 기본 산정 | `probability`, `severity`, `risk_level`, `residual_risk_level` |

---

## 5. 위험성 등급 v1 기본 산정 방식

| 구분 | 빈도 | 강도 | 위험도 | 등급 |
|------|------|------|--------|------|
| 일반 hazard | 3 | 3 | 9 | 중 |
| 중대위험 hazard* | 3 | 4 | 12 | 높음 |
| 감소대책 후 (공통) | 2 | 2 | 4 | 낮음 |

*중대위험: FALL_FROM_HEIGHT, CONFINED_SPACE_ASPHYXIATION, ELECTRIC_SHOCK, HOT_WORK_FIRE, HEAVY_LIFTING

**중요:** 위험성 등급은 v1 기본 산정값이며, 현장 실측·작업방법·인원·장비 조건에 따라 조정 필요.

---

## 6. 공종 + 공통 고위험작업 병합 예시

```python
from engine.recommendation.risk_assessment_adapter import build_ra001_input_from_trade_id

payload = build_ra001_input_from_trade_id(
    trade_id="FIRE_PIPE_INSTALL",
    common_work_ids=["COMMON_HOT_WORK", "COMMON_WORK_AT_HEIGHT"],
    site_context={"site_name": "테스트 현장", "work_location": "지하1층"},
)
# payload["rows"] → 11행 (중복 hazard 제거)
# payload["_meta"]["source_trace"] → ["FIRE_PIPE_INSTALL", "COMMON_HOT_WORK", "COMMON_WORK_AT_HEIGHT"]
```

CLI:

```bash
python scripts/dry_run_trade_to_ra001.py \
  --trade-id FIRE_PIPE_INSTALL \
  --common-work COMMON_HOT_WORK \
  --common-work COMMON_WORK_AT_HEIGHT \
  --site-name "테스트 현장" \
  --work-location "지하1층" \
  --output-xlsx /tmp/ra001_fire.xlsx
```

---

## 7. 소방 배관 예시 (FIRE_PIPE_INSTALL)

- rows: 7행 (FALL_FROM_HEIGHT, FALLING_OBJECT, CAUGHT_BETWEEN, HOT_WORK_FIRE, CUT_GRINDING, HEAVY_LIFTING, ELECTRIC_SHOCK)
- 필수서류: RA-001, RA-004, ED-003
- 필수허가서: PTW-002, PTW-003
- 필수교육: EDU_SPECIAL_16H, EDU_CONSTRUCTION_BASIC, EDU_TBM
- 중대위험 등급 높음: FALL_FROM_HEIGHT(12), HOT_WORK_FIRE(12), HEAVY_LIFTING(12), ELECTRIC_SHOCK(12)

---

## 8. 전기 케이블 트레이 예시 (ELEC_CABLE_TRAY)

- rows: 5행 (FALL_FROM_HEIGHT, FALLING_OBJECT, ELECTRIC_SHOCK, HEAVY_LIFTING, CAUGHT_BETWEEN)
- 필수허가서: PTW-003, PTW-004
- 중대위험: FALL_FROM_HEIGHT, ELECTRIC_SHOCK, HEAVY_LIFTING

---

## 9. 기계 배관 예시 (MECH_PIPE_INSTALL)

- rows: 6행 (FALL_FROM_HEIGHT, FALLING_OBJECT, CAUGHT_BETWEEN, HOT_WORK_FIRE, HEAVY_LIFTING, CUT_GRINDING)
- 필수허가서: PTW-002, PTW-003
- 중대위험: FALL_FROM_HEIGHT, HOT_WORK_FIRE, HEAVY_LIFTING

---

## 10. 필수 고정 문구 (3개)

Excel "주의사항" 시트에 항상 포함:

1. "본 위험성평가표는 공종별 프리셋 기반 초안이며, 현장 조건에 따라 관리감독자 및 작업자가 검토·보완해야 한다."
2. "위험성 등급은 v1 기본 산정값이며, 현장 실측·작업방법·인원·장비 조건에 따라 조정한다."
3. "관련 법령 및 서류는 현행 원문과 발주처/원청 기준을 확인 후 적용한다."

---

## 11. 현재 한계

| 항목 | 상태 |
|------|------|
| 위험성 등급 현장 맞춤 산정 | 미구현 (v1 기본값 고정) |
| site_context 활용 (등급 보정) | 미구현 |
| conditional_permits 자동 반영 | 미구현 |
| 법령 조항 직접 참조 (legal_basis) | 부분 구현 (document_id 참조만) |
| skeleton 공종 (건축/토목/철골/해체) | NEEDS_VERIFICATION — 사용 불가 |
| UI 연결 | 미구현 |
| API 엔드포인트 | 미구현 |

---

## 12. 다음 단계 후보

1. **위험성 등급 현장 맞춤 산정** — 빈도·강도 매트릭스 입력값 수신
2. **conditional_permits 자동 반영** — site_context의 작업 조건 기반 허가서 추가
3. **RA-004 TBM 일지 연결** — trade_risk_recommendation payload → TBM 일지 자동 생성
4. **API 엔드포인트** — `POST /api/v1/forms/risk-assessment` (payload → xlsx)
5. **skeleton 공종 상세화** — 건축/토목/철골/해체 NEEDS_VERIFICATION → PARTIAL_VERIFIED
