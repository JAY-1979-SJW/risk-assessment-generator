# work_types — 공종별 위험성평가 프리셋

공종별 위험요인·감소대책·필요서류·교육·장비·작업허가서 매핑 프리셋 마스터.

## 파일 목록

| 파일 | 공종 그룹 | 상태 |
|---|---|---|
| `trade_presets.yml` | 전체 공종 인덱스 | v1 |
| `firefighting_work_types.yml` | 소방설비 | 상세 데이터 |
| `electrical_work_types.yml` | 전기 | 상세 데이터 |
| `mechanical_work_types.yml` | 기계설비 | 상세 데이터 |
| `common_high_risk_work_types.yml` | 공통 고위험작업 | 상세 데이터 |
| `architecture_work_types.yml` | 건축 | skeleton |
| `civil_work_types.yml` | 토목 | skeleton |
| `steel_structure_work_types.yml` | 철골 | skeleton |
| `demolition_work_types.yml` | 해체 | skeleton |

## trade_id 규칙

`{그룹접두어}_{작업명_영문}` 형식 (대문자 + 언더스코어)

- 소방: `FIRE_`
- 전기: `ELEC_`
- 기계설비: `MECH_`
- 공통 고위험: `COMMON_`
- 건축: `ARCH_`
- 토목: `CIVIL_`
- 철골: `STEEL_`
- 해체: `DEMO_`

## 참조 관계

- `default_hazards` → `hazards/hazard_master.yml`의 `hazard_id`
- `required_documents` / `recommended_documents` / `required_permits` → `documents/document_catalog.yml`의 ID
- `required_trainings` → `training/training_types.yml`의 `training_code`
