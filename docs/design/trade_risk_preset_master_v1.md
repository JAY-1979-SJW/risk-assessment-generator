# 공종별 위험성평가 프리셋 마스터 v1

작성일: 2026-04-25  
버전: 1.0  
상태: 소방/전기/기계/공통 고위험 VERIFIED, 건축/토목/철골/해체 SKELETON

---

## 1. 목적

공종(작업 유형)을 선택하면 위험성평가표 작성에 필요한 요소를 자동 추천하는 데이터 레이어.  
"위험성평가표 완성본 하드코딩"이 아니라, **공종 → 프리셋 조회 → 위험성평가 초안 생성** 흐름을 지원하는 마스터 데이터다.

---

## 2. 데이터 구조

### 2.1 디렉토리

```
data/masters/safety/
├── hazards/
│   ├── hazard_master.yml        # 20종 위험요인 정의
│   ├── hazard_controls.yml      # 12종 표준 감소대책 상세
│   └── README.md
├── work_types/
│   ├── trade_presets.yml        # 전체 공종 인덱스 (54종)
│   ├── firefighting_work_types.yml   # 소방설비 10종
│   ├── electrical_work_types.yml     # 전기 9종
│   ├── mechanical_work_types.yml     # 기계설비 9종
│   ├── common_high_risk_work_types.yml  # 공통 고위험작업 10종
│   ├── architecture_work_types.yml   # 건축 5종 (skeleton)
│   ├── civil_work_types.yml          # 토목 4종 (skeleton)
│   ├── steel_structure_work_types.yml # 철골 4종 (skeleton)
│   ├── demolition_work_types.yml     # 해체 3종 (skeleton)
│   └── README.md
└── mappings/
    ├── trade_document_mapping.yml   # 공종 → 필요 서류 역색인
    ├── trade_training_mapping.yml   # 공종 → 필요 교육 역색인
    ├── trade_equipment_mapping.yml  # 공종 → 주요 장비 역색인
    └── trade_permit_mapping.yml     # 공종 → 작업허가서 역색인
```

### 2.2 trade 스키마 (상세 공종)

```yaml
- trade_id: FIRE_PIPE_INSTALL          # 대문자+언더스코어, 그룹 접두어 포함
  trade_name: 소방배관 설치
  trade_group: 소방설비
  description: 스프링클러·옥내소화전 배관 설치 작업
  enabled: true
  priority: 1                          # 1=최우선, 2=일반, 3=참고
  default_hazards:                     # hazard_master.yml ID 목록
    - FALL_FROM_HEIGHT
    - HOT_WORK_FIRE
  required_documents:                  # document_catalog.yml ID 목록
    - RA-001
    - RA-004
    - ED-003
  recommended_documents: [...]
  required_trainings:                  # training_types.yml code 목록
    - EDU_SPECIAL_16H
  required_permits:                    # PTW-xxx ID 목록
    - PTW-002
  common_equipment: [...]
  ppe: [...]
  source_status: VERIFIED              # VERIFIED/PARTIAL_VERIFIED/NEEDS_VERIFICATION/PRACTICAL
  notes: ""
```

### 2.3 hazard_id 코드 체계 (20종)

| hazard_id | 위험요인 |
|-----------|---------|
| FALL_FROM_HEIGHT | 고소 추락 |
| FALLING_OBJECT | 낙하·비래 |
| SLIP_TRIP | 전도·미끄러짐 |
| CAUGHT_BETWEEN | 끼임 |
| STRUCK_BY_EQUIPMENT | 장비 충돌 |
| HOT_WORK_FIRE | 화기작업 화재·폭발 |
| ELECTRIC_SHOCK | 감전 |
| ARC_FLASH | 아크 플래시 |
| CONFINED_SPACE_ASPHYXIATION | 밀폐공간 질식 |
| OXYGEN_DEFICIENCY | 산소결핍 |
| TOXIC_GAS | 유해가스 |
| HEAVY_LIFTING | 중량물 인양 |
| MANUAL_HANDLING | 근골격계 부담 |
| NOISE_DUST | 소음·분진 |
| CHEMICAL_EXPOSURE | 화학물질 노출 |
| GAS_CYLINDER | 가스 용기 폭발 |
| CUT_GRINDING | 절단·연삭 |
| ROTATING_PARTS | 회전체 |
| EXCAVATION_COLLAPSE | 굴착 붕괴 |
| VEHICLE_TURNOVER | 차량 전복 |

### 2.4 mapping 파일 역할

| 파일 | 키 | 값 |
|------|----|----|
| trade_document_mapping.yml | trade_id | required/recommended/conditional_documents |
| trade_training_mapping.yml | trade_id | required_trainings, special_training_topics |
| trade_equipment_mapping.yml | trade_id | common_equipment, equipment_documents, inspection_documents |
| trade_permit_mapping.yml | trade_id | required_permits, conditional_permits(조건 포함) |

---

## 3. 공종 선택 시 자동 추천 흐름

```
사용자: 공종 선택 (예: FIRE_PIPE_INSTALL)
        ↓
[1] work_types/firefighting_work_types.yml 조회
    → default_hazards, required_documents, required_permits, required_trainings 로드
        ↓
[2] mappings/ 역색인 조회 (4개 파일)
    → 조건부 허가서·서류·교육 후보 목록 제시
        ↓
[3] hazards/hazard_master.yml → hazard_controls.yml 조회
    → 각 hazard별 표준 감소대책(CTRL_xxx) 로드
        ↓
[4] 위험성평가 초안 생성
    → RA-001(위험성평가표) 행 자동 채움: 위험요인, 감소대책, 필요서류 연결
        ↓
[5] 사용자 검토·수정 후 확정
```

---

## 4. 공종별 예시

### 4.1 소방설비 — FIRE_WELDING_CUTTING (소방용접·용단)

- **필수 서류**: RA-001, RA-004, ED-003, PTW-002
- **필수 허가서**: PTW-002 (화기작업 허가서)
- **필수 교육**: EDU_SPECIAL_16H, EDU_TBM
- **주요 위험요인**: HOT_WORK_FIRE, FALL_FROM_HEIGHT, CUT_GRINDING, GAS_CYLINDER
- **핵심 감소대책**: 용접 전 인화물질 제거, 소화기 비치, 불꽃 비산 방지포, 안전대

### 4.2 전기 — ELEC_LIVE_PROXIMITY_WORK (활선 근접 작업)

- **필수 서류**: RA-001, RA-004, ED-003, PTW-004
- **필수 허가서**: PTW-004 (전기작업 허가서)
- **필수 교육**: EDU_SPECIAL_16H, EDU_TBM
- **주요 위험요인**: ELECTRIC_SHOCK, ARC_FLASH
- **핵심 감소대책**: LOTO(잠금·태그), 절연장갑, 절연공구, 활선 경고표지

### 4.3 기계설비 — MECH_CHILLER_BOILER_ROOM (냉동기·보일러실 작업)

- **필수 서류**: RA-001, RA-004, ED-003
- **필수 허가서**: PTW-004 (전기작업)
- **조건부**: PTW-001 (밀폐공간 기준 충족 시)
- **필수 교육**: EDU_SPECIAL_16H, EDU_CONFINED_SPACE, EDU_TBM
- **주요 위험요인**: CONFINED_SPACE_ASPHYXIATION, TOXIC_GAS, ELECTRIC_SHOCK

### 4.4 공통 고위험 — COMMON_CONFINED_SPACE (밀폐공간 작업)

- **필수 서류**: RA-001, RA-004, ED-003, WP-014, PTW-001
- **필수 허가서**: PTW-001 (밀폐공간 작업 허가서)
- **필수 교육**: EDU_CONFINED_SPACE, EDU_TBM
- **주요 위험요인**: CONFINED_SPACE_ASPHYXIATION, OXYGEN_DEFICIENCY, TOXIC_GAS

---

## 5. RA-001 연동 예정 흐름 (미구현)

현재 이 마스터 데이터는 독립 데이터 레이어로만 존재한다.  
향후 RA-001 builder가 구현될 때 아래 방식으로 연동 예정:

```python
# 예정 API (미구현)
preset = load_trade_preset("FIRE_PIPE_INSTALL")
ra_rows = []
for hazard_id in preset["default_hazards"]:
    controls = load_hazard_controls(hazard_id)
    for ctrl in controls:
        ra_rows.append({
            "위험요인": hazard.name,
            "현재_안전조치": ctrl.current_measures,
            "추가_안전조치": ctrl.additional_measures,
            "감소대책": ctrl.description,
        })
generate_ra_001_excel(ra_rows, ...)
```

---

## 6. 현재 한계

| 항목 | 상태 | 비고 |
|------|------|------|
| 소방설비 10종 | VERIFIED | document/training/permit 3중 무결성 검증 완료 |
| 전기 9종 | VERIFIED | 동일 |
| 기계설비 9종 | VERIFIED | 동일 |
| 공통 고위험 10종 | VERIFIED | 동일 |
| 건축 5종 | SKELETON | 상세 데이터 미입력 |
| 토목 4종 | SKELETON | 상세 데이터 미입력 |
| 철골 4종 | SKELETON | 상세 데이터 미입력 |
| 해체 3종 | SKELETON | 상세 데이터 미입력 |
| RA-001 builder | 미구현 | 이 마스터 데이터 활용 예정 |
| 위험성 등급 산정 | 미구현 | 빈도×강도 매트릭스 연동 예정 |

---

## 7. 다음 단계

1. **건축/토목/철골/해체 skeleton 상세화** — 법령 원문 확인 후 VERIFIED 전환
2. **RA-001 builder 구현** — 이 마스터 데이터를 입력으로 활용
3. **위험성 등급 매트릭스 연동** — risk_scoring_rule.md 참조
4. **공종-위험요인 역색인 추가** — 위험요인 → 관련 공종 조회 지원
5. **hazard_id 확장** — COLLAPSE_STRUCTURE(구조물 붕괴), DROWNING(익수) 등 추가 검토
