# hazards — 위험요인 마스터

건설현장 안전관리에서 사용하는 위험요인(Hazard) 코드 마스터.

## 파일 목록

| 파일 | 설명 |
|---|---|
| `hazard_master.yml` | 위험요인 코드 마스터 (HZ_xxx) |

## 코드 체계

- 접두어: `HZ_`
- 카테고리: FALL / COLLAPSE / CAUGHT_IN / STRUCK_BY / ELECTRIC / FIRE_EXPLOSION / ASPHYXIATION / HEALTH / ERGONOMIC
- 예시: `HZ_FALL_HEIGHT`, `HZ_COLLAPSE_FORMWORK`

## 참조 관계

- `work_types/trade_risk_presets.yml` → `hazard_code` 참조
- `mappings/trade_hazard_mapping.yml` → `hazard_code` 참조
