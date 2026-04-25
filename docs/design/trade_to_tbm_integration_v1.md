# trade_risk_recommendation → TBM 안전점검 일지 연동 설계 v1

작성일: 2026-04-25

---

## 목적

공종별 위험성평가 추천 엔진(`trade_risk_recommender`)이 생성한 `trade_risk_recommendation` payload를 입력으로 받아, RA-004 TBM 안전점검 일지 Excel을 자동 생성한다.

사용자(관리감독자)가 `trade_id`를 선택하면 해당 공종의 위험요인·감소대책·작업 전 확인사항·작업허가서 확인사항이 반영된 TBM 일지 초안이 생성된다.

---

## 입력 흐름

```
trade_id (+ optional: common_work_ids, site_context)
    ↓
trade_risk_recommender.build_trade_risk_recommendation()
    ↓
recommendation payload (risk_items, required_permits, ppe, ...)
    ↓
tbm_log_adapter.build_tbm_input_from_trade_recommendation()
    ↓
TBM 입력 dict (tbm_log_builder 호환)
    ↓
tbm_log_builder.build_tbm_log_excel()
    ↓
TBM 안전점검 일지 .xlsx
```

편의 함수 `build_tbm_input_from_trade_id(trade_id, ...)` 가 전체 흐름을 단일 호출로 처리한다.

---

## trade_risk_recommendation payload 구조

```python
{
    "trade_id": "FIRE_PIPE_INSTALL",
    "trade_name": "소방 배관 설치",
    "trade_group": "소방설비",
    "site_context": {
        "site_name": None,
        "work_location": None,
        "work_date": None,
        "workers_count": None,
        "equipment_used": [],
    },
    "risk_items": [
        {
            "hazard_id": "FALL_FROM_HEIGHT",
            "hazard_name": "추락",
            "category": "FALL",
            "risk_scenario": "소방 배관 설치 작업 중 추락 발생 가능",
            "typical_causes": [...],
            "typical_consequences": [...],
            "controls": [
                {"control_type": "ENGINEERING", "priority": 1, "description": "안전난간 설치 ...", ...},
                ...
            ],
            "related_documents": ["PTW-003", "CL-007"],
            "source_trade_ids": ["FIRE_PIPE_INSTALL"],
            "source_status": "PARTIAL_VERIFIED",
        },
        ...
    ],
    "required_documents": ["RA-001", "RA-004", "ED-003"],
    "recommended_documents": [...],
    "required_trainings": ["EDU_SPECIAL_16H", "EDU_CONSTRUCTION_BASIC", "EDU_TBM"],
    "required_permits": ["PTW-002", "PTW-003"],
    "common_equipment": ["welding_machine", "grinder", "chain_block", "aerial_work_platform"],
    "ppe": ["safety_helmet", "safety_harness", "safety_gloves", "safety_shoes", "welding_face_shield"],
    "warnings": [],
    "source_trace": ["FIRE_PIPE_INSTALL"],
    "source_status_summary": {"PARTIAL_VERIFIED": 7, ...},
}
```

---

## TBM 입력 변환 구조

```python
{
    # tbm_log_builder required
    "tbm_date": "YYYY-MM-DD HH:MM",   # site_context.work_date 또는 빈칸
    "today_work": "소방 배관 설치 작업",
    "hazard_points": "• 추락: ...\n• 낙하물: ...",
    "safety_instructions": "• 안전난간 설치 ...\n• 추락방지망 설치 ...",

    # tbm_log_builder optional
    "site_name": "",
    "project_name": "",
    "tbm_location": "",               # site_context.work_location
    "trade_name": "소방 배관 설치",
    "pre_work_checks": "• [서류] RA-001 확인\n...",
    "permit_check": "• [필수] PTW-002 허가서 번호 ...",
    "ppe_check": "• safety_helmet\n...",
    "worker_opinion": "",
    "action_items": "",
    "attendees": [],

    # 확장 메타 (builder 미전달, 검증·감사용)
    "supervisor_signature": "",
    "training_notes": "• 필수 교육 이수 확인: EDU_SPECIAL_16H\n...",
    "photo_evidence": {
        "TBM_MEETING": "RECOMMENDED",
        "WORK_AREA_BEFORE": "RECOMMENDED",
        "PPE_CHECK": "OPTIONAL",
        "PERMIT_OR_CHECKLIST": "OPTIONAL",
    },
    "fixed_notices": [...],           # 4개 고정 문구
    "_meta": {...},                   # 원본 추천 메타 보존
}
```

---

## 위험요인 공유 방식

`risk_items`의 각 항목을 다음 형식으로 변환한다:

```
• {hazard_name}: {risk_scenario}
```

- `risk_scenario`가 없으면 `• {hazard_name}` 만 표시
- 공통 고위험작업 merge 시 중복 hazard_id는 제거됨 (recommender 수준 처리)

---

## 안전작업 지시사항 생성 방식

모든 `risk_items`의 `controls`를 수집해 `priority` 오름차순으로 정렬하고 `description`만 추출한다:

```
• {control.description}
```

- 동일 description 중복 제거
- control_type 접두어 제외 (TBM 열람자인 작업자 가독성 우선)
- priority 1(ENGINEERING) → 2(ADMINISTRATIVE) → 3(PPE) 순으로 노출

---

## 작업 전 확인사항 생성 방식

```
[서류] {required_documents 각 항목} 확인
[참고서류] {risk_items.related_documents, required_documents 미포함분} 확인
[권장서류] {recommended_documents 상위 3개, 위 목록 미포함분} 확인
[장비] {common_equipment 각 항목} 사전 점검
[보호구] {ppe 각 항목} 착용 확인
```

---

## 작업허가서 확인사항 생성 방식

`required_permits` 목록을 다음 형식으로 변환한다:

```
• [필수] {permit_id} 허가서 번호 및 유효기간 확인
```

- `conditional_permits`는 v1에서 자동 반영하지 않고 `_meta.warnings`에 기록
- 허가서가 없으면 `permit_check` 필드는 빈 문자열

---

## 사진 증빙 정책

| 항목 | 상태 | 비고 |
|------|------|------|
| TBM_MEETING | RECOMMENDED | TBM 실시 증빙 |
| WORK_AREA_BEFORE | RECOMMENDED | 작업 전 현장 상태 확인 |
| PPE_CHECK | OPTIONAL | 보호구 착용 확인 |
| PERMIT_OR_CHECKLIST | OPTIONAL | 허가서·점검표 사진 |

**사진은 법정 필수 고정항목이 아닌 점검 대응 권장 증빙이다.**

---

## 고정 문구 (4개)

1. 본 TBM 일지는 작업 전 위험요인 공유 및 안전작업 지시 기록이며, 법정 안전보건교육 수료증을 대체하지 않는다.
2. 본 내용은 공종별 프리셋 기반 초안이며, 현장 조건에 따라 관리감독자와 근로자가 검토·보완해야 한다.
3. 작업허가서, 점검표, 보호구, 장비 상태는 작업 전 현장에서 최종 확인한다.
4. TBM 사진은 법정 필수 고정항목이 아니라 점검 대응을 위한 권장 증빙으로 관리한다.

---

## RA-001과의 관계

| 항목 | RA-001 (위험성평가표) | TBM 일지 |
|------|----------------------|----------|
| 목적 | 위험성평가 기록 (법정) | 작업 전 안전 브리핑 (실무 권장) |
| 대상 | 관리감독자·안전관리자 | 관리감독자·작업자 |
| 위험요인 상세 | 빈도×강도 등급 포함 | 상황 중심 텍스트 |
| 감소대책 | control_type·priority 표시 | 작업지시 문장 형태 |
| 공통 입력 | risk_items (동일 소스) | risk_items (동일 소스) |
| 서명란 | 작업자 서명 없음 | 참석자 20명 + 관리감독자 서명란 |

두 서식은 동일한 `recommendation` payload에서 독립적으로 생성된다. 어느 쪽도 다른 쪽을 대체하지 않는다.

---

## 소방 배관 TBM 예시 (FIRE_PIPE_INSTALL)

```
공종: 소방 배관 설치
위험요인: 7개 (추락·낙하물·협착·화재·절단·중량물·감전)
안전수칙: 29개
필수 허가서: PTW-002(화기), PTW-003(고소)
필수 교육: EDU_SPECIAL_16H, EDU_CONSTRUCTION_BASIC, EDU_TBM
Excel: 약 8,200 bytes
```

---

## 전기 케이블 트레이 TBM 예시 (ELEC_CABLE_TRAY)

```
공종: 전기 케이블 트레이 설치
위험요인: 5개 (감전·추락·협착·낙하물·중량물)
안전수칙: 22개
필수 허가서: PTW-003(고소), PTW-004(전기)
Excel: 약 7,900 bytes
```

---

## 기계 배관 TBM 예시 (MECH_PIPE_INSTALL)

```
공종: 기계 배관 설치
위험요인: 6개 (추락·낙하물·화재·중량물·협착·감전)
안전수칙: 24개
필수 허가서: PTW-002(화기), PTW-003(고소)
Excel: 약 8,000 bytes
```

---

## 현재 한계

1. `conditional_permits` 자동 반영 미구현 — `_meta.warnings`에 기록만 됨
2. `work_description`은 adapter 내부 처리만 가능 (recommender site_context 표준 외)
3. 참석자 명단·서명은 현장 직접 입력 필요 — 프리셋으로 생성 불가, `attendees: []` 빈 서명란으로 출력됨
4. 위험요인 우선순위 정렬 없음 (출현 순서 그대로)
5. `training_notes`는 `_meta` 내 보관; tbm_log_builder에 별도 렌더 셀 없음

---

## 서식 구현 우선순위 원칙

새 서식 builder를 구현하기 전에 반드시 아래 순서로 근거를 확인한다.

1. **법령 별지 서식** — 산업안전보건법·시행규칙·고시에 별지 서식이 지정된 경우 우선 참조
2. **고용노동부 자료** — 고시·예규·지침에 서식 예시가 있으면 참조
3. **KOSHA GUIDE** — 한국산업안전보건공단 가이드라인의 권고 서식 참조
4. **발주처·원청 실무서식** — 현장 관행 서식
5. **자체 표준서식** — 위 1~4에 근거가 없을 때만 자체 서식으로 구현

근거 미확정 항목은 `source_status: NEEDS_VERIFICATION`으로 처리하고, 확인 전 VERIFIED로 격상하지 않는다.

---

## 다음 단계 원칙 (PTW-002 화기작업 허가서)

PTW-002 builder를 구현하기 전에 다음 항목을 먼저 확인한다.

| 확인 항목 | 기준 | 상태 |
|-----------|------|------|
| 법정 별지 서식 존재 여부 | 산안법 시행규칙, 고시 별지 | 미확인 |
| 고용노동부 자료 | 화기작업 관련 고시·지침 | 미확인 |
| KOSHA GUIDE 서식 | W-2-2023 등 | 미확인 |
| 발주처·원청 실무서식 | 현장 관행 | 미확인 |

법정 별지 서식이 없음이 확인된 경우에만 KOSHA GUIDE 또는 실무서식 기반으로 구현한다.

---

## 다음 단계 후보

- **PTW-002 화기작업 허가서** — 구현 전 법정 별지 서식 존재 여부 확인 단계를 먼저 수행
- 대공종·중공종·세부작업·작업일보 분류 마스터 v1 구축
- TBM 일지 builder에 training_notes 렌더 셀 추가 (action_items 활용 또는 신규 섹션)
- conditional_permits 자동 반영 로직 추가
