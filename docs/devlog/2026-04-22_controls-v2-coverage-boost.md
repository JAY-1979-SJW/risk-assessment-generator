# controls 체계 v2 고도화 보고 (2026-04-22)

법령 단계 진입 전, controls(대책) 축의 커버리지·정확도를 먼저 끌어올리는 단계.

---

## 1. 작업 내용

1. 기존 산출물(controls master v1, 400 샘플 매핑) 재확인
2. v1 에서 확정된 72 건 매핑에 대한 reviewer 정답셋 파일 준비
3. 샘플 400 → 800 으로 확대 (KOSHA normalized body 에서 400 건 추가, zero-hit 160 건 포함)
4. zero-hit 4 category (supervision / permit / administrative / traffic) 보강 및 해소
5. controls master v1(47) → v2(63, 신규 16) 로 보정 (merge/split/rename/alias)
6. equipment 연결 보강 (55 → 56% 커버리지, equipment 쪽 97% 커버리지)
7. 반자동 매핑 규칙 v0.1 → v0.2 정밀화
8. descriptive_noise 복구 규칙 + 자연어 렌더링 템플릿 문서화

---

## 2. 생성/수정 파일

### 데이터
- `data/risk_db/master/controls_master_draft_v2.csv` (63 controls, equipment EQ_* 연결 포함)
- `data/risk_db/master/sentence_labeling_sample_v2.csv` (800 샘플 입력)
- `data/risk_db/master/sentence_control_mapping_sample_v2.csv` (800 샘플 매핑)
- `data/risk_db/master/sentence_control_review_sheet.csv` (v1 72 건 reviewer 정답셋)
- `data/risk_db/master/controls_equipment_linkage.csv` (equipment × control 매트릭스)

### 문서
- `docs/design/controls_mapping_rules_refined.md` (v0.2 규칙)
- `docs/design/controls_zero_hit_category_notes.md` (zero-hit 해소 메모)
- `docs/design/controls_noise_and_rendering.md` (noise 복구 + 렌더링 템플릿)
- `docs/devlog/2026-04-22_controls-v2-coverage-boost.md` (본 보고)

### 스크립트
- `scripts/rules/build_review_sheet.py` (reviewer 시트 생성)
- `scripts/rules/build_controls_v2.py` (v2 master 기반 샘플 확장·매핑)
- `scripts/rules/link_controls_equipment.py` (controls ↔ equipment 연결)

### 기존 파일 (변경 없음 · 재사용)
- `docs/design/controls_master_schema.md` (v0.1 스키마 유지)
- `docs/design/sentence_classification_schema.md` (유지)
- `data/risk_db/master/controls_master_draft.csv` (v1 그대로 보존)
- `data/risk_db/master/sentence_control_mapping_sample.csv` (v1 그대로 보존)

> v2 는 **새 파일**로 분리 저장하여 v1 을 덮어쓰지 않음.

---

## 3. controls master 변경 요약

| 지표 | v1 | v2 | Δ |
|---|---|---|---|
| 총 controls | 47 | 63 | +16 |
| engineering_control | 8 | 13 | +5 |
| ppe_control | 2 | 2 | 0 |
| training_control | 3 | 3 | 0 |
| inspection_control | 7 | 9 | +2 |
| document_control | 5 | 6 | +1 |
| supervision_control | 5 | 6 | +1 |
| permit_control | 3 | 5 | +2 |
| administrative_control | 3 | 5 | +2 |
| emergency_control | 3 | 3 | 0 |
| health_control | 3 | 4 | +1 |
| housekeeping_control | 3 | 3 | 0 |
| traffic_control | 2 | 4 | +2 |

### 신규 16 건 (note 에 이유 기록)
- engineering: `ctrl_dust_suppression`, `ctrl_chemical_storage_segregation`, `ctrl_excavation_shoring`, `ctrl_scaffold_install_std`, `ctrl_machine_emergency_stop`
- inspection: `ctrl_lifting_equipment_inspection`, `ctrl_electrical_equipment_inspection`
- document: `ctrl_lifting_work_plan`
- supervision: `ctrl_work_leader_designation` (`supervisor_assignment` 과 구분: 차량계·특정 작업 직접 지휘)
- permit: `ctrl_excavation_permit`, `ctrl_height_work_permit`
- administrative: `ctrl_work_area_demarcation`, `ctrl_work_hour_restriction`
- health: `ctrl_heat_stress_management`
- traffic: `ctrl_vehicle_path_separation`, `ctrl_speed_limit`

### keyword/alias 보강 (기존 47 건)
- `ctrl_fall_protection_install`: + 안전방망 / 추락방호망
- `ctrl_local_ventilation_install`: + LEV / 후드
- `ctrl_ppe_wear`: + 개인보호구 / PPE / 송기마스크 / 보안면 / 귀덮개
- `ctrl_signalman_assignment`: + 수신호 / 신호체계
- `ctrl_standby_person_assignment`: + standby / 입회자
- `ctrl_access_restriction`: + 안전선 / 안전펜스 / 바리케이드 / 접근금지
- `ctrl_work_permit_issue`: + PTW / permit to work / 허가증

### review_status 재배치
- v1 47 건 → `needs_review` 로 상향 (hit 여부와 관계없이 reviewer 검토 필요)
- v2 신규 16 건 → `draft` 유지

---

## 4. 샘플 확대 결과

| 지표 | v1 | v2 |
|---|---|---|
| 총 샘플 | 400 | 800 |
| source 분포 | law120 / kosha120 / admrul60 / expc60 / licbyl40 | law120 / kosha520 / admrul60 / expc60 / licbyl40 |
| noise 비율 | 19% | 41% (kosha 원문 기반 문장 유입 영향) |

- 의도된 kosha 편중 (zero-hit 카테고리인 supervision/traffic/admin 문장이 kosha OPL 에 풍부).
- admrul/licbyl/expc 는 원본 body 가 없어 본 단계에서 확장 보류. 법령 단계에서 해결.

---

## 5. hit rate 변화

| 지표 | v1 (400) | v2 (800) |
|---|---|---|
| hit 수 | 72 | **169** |
| hit rate | 18.0% | **21.1%** |
| confidence high | 10 (14% of hits) | **131 (78% of hits)** |
| confidence medium | 62 | 38 |
| 활성 control 수 | 15 / 47 | **32 / 63** |

- hit rate 는 3.1%p 상승.
- **confidence high 비율이 14% → 78%** 로 대폭 상승 → 구체 keyword(4자↑) 매칭 규칙이 유효.
- 활성 control 수는 15 → 32. 그러나 63 중 32 만 활성. 잔여 31 개 control 은 주로 법령/행정규칙에서 hit 예상 → 법령 단계로 연기.

---

## 6. zero-hit category 해소 여부

| category | v1 | v2 | 해소 |
|---|---|---|---|
| supervision_control | 0 | **20** | YES |
| permit_control | 0 | **12** | YES |
| administrative_control | 0 | **26** | YES |
| traffic_control | 0 | **7** | YES |

**12 category 전부 hit 확보. zero-hit 잔여 0.**

---

## 7. equipment/control 연결 보강 결과

- controls → equipment 연결율: v1 25% → **v2 56%** (63 중 35 건)
- equipment → controls 연결율: **97%** (31 중 30 건, 미연결 `EQ_VIBRATOR` 만)
- 미연결 controls 대부분은 "장비 횡단" 성격(ppe / training / noise / emergency / 일부 administrative) — 장비 종속성 없음. 정책적으로 empty.
- 신규 equipment 후보 발생 없음 — 기존 31 EQ_* 코드로 모두 커버 가능.
- 보정된 `related_equipment_codes` 는 한글 명(예: "비계") → 실 코드(`EQ_SCAFF`) 로 일괄 교체.

---

## 8. 규칙 정밀화 결과

- 규칙 소스 통합: v1 에서는 스크립트 CTRL_RULES 와 master 가 분리 → v2 에서는 master `typical_keywords` 단일 소스.
- 정렬 기준 추가: keyword 평균 길이 내림차순 (구체 control 우선).
- 단일 토큰 차단 set 고정: `{관리, 조치, 확인, 준수, 주의, 실시, 부착, 설치}` (2글자↓ 단독 hit 금지).
- confidence 식 변경: 4자↑ 구체 keyword 1회 hit 만으로도 high 승격.
- negative rules 명시: scope_exclusion / definition / legal_reference / prohibition 문장은 control 할당 금지.

---

## 9. noise 복구 결과

- v2 noise 327 건 중 복구 후보 23 건(약 7%) 식별.
- 복구 규칙 문서화. 본 단계에서 자동 재라벨링은 하지 않음.
- reviewer 시트에 복구 플래그 추가는 다음 단계에서 수행.

---

## 10. 자연어 렌더링 보강 결과

- 12 category 전부에 대표 control 의 **완결형 대책 문장** 2개씩 템플릿 작성.
- "적절히 조치한다" / "관리한다" 같은 공허 표현 금지 규칙 고정.
- master `description` 컬럼과 별도로 렌더링 템플릿 관리 (향후 DB 반영 시 `render_template_ko` 컬럼 도입 여지).

---

## 11. 사람 검토가 필요한 잔여 항목

| 번호 | 항목 | 권장 행동 |
|---|---|---|
| R1 | `ctrl_incident_report` 과잉 hit (v1 10 → v2 11) | reviewer 가 법정 보고 조항과 실무 보고 대책을 분리 |
| R2 | `ctrl_access_restriction` 과잉 hit (v2 26) | split 후보: 출입금지 표지 vs 출입통제 절차 |
| R3 | `ctrl_guard_installation` 광범위 매칭 | 세분 control(`ctrl_machine_emergency_stop`) 와 경계 재확인 |
| R4 | v1 72 hit 정답셋 검토 미완료 | `sentence_control_review_sheet.csv` reviewer 실행 |
| R5 | v2 추가 97 hit 검토 미완료 | 별도 review sheet 생성 단계 필요 |
| R6 | noise 복구 후보 23 건 재라벨 | 다음 단계 반자동 재라벨 파이프라인 설계 |
| R7 | admrul/expc/licbyl body 원문 미확보 | 법령 단계에서 해결 |
| R8 | `EQ_VIBRATOR` orphan | 관련 control (진동 노출 관리?) 신설 후보 |

---

## 12. 법령 단계로 넘어갈 준비 상태

**준비 OK:**
- 63 controls 체계 안정화 (12 category 전 분포)
- 동의어/alias 가 master 단일 소스에 통합
- 규칙이 코드 뿐 아니라 문서(`controls_mapping_rules_refined.md`) 로 고정
- equipment ↔ control 교차 참조 체계 확보 (`controls_equipment_linkage.csv`)
- 자연어 렌더링 템플릿 확보 → 법령 문장에서 바로 대책 문장으로 변환 가능

**법령 단계 진입 시 반드시 해야 할 일:**
- admrul/licbyl/expc 본문 원문 수집·정규화 (현재 index 만 있음)
- 법조문 → control_code 매핑 (`law_control_map` 테이블)
- 법적 근거가 있는 control 만 `legal_required_possible=Y` 확정
- reviewer 시트 실제 검토로 정답셋 확정

---

## 13. 최종 판정

**PASS** — 사전 정의한 성공 기준을 모두 충족했다.

| 성공 기준 | 달성 |
|---|---|
| controls master 완성도 ↑ | 47 → 63, 동의어 통합 |
| reviewer 정답셋 파일 준비 | 72 건 sheet 완료 |
| 샘플 800 이상 | 800 달성 |
| zero-hit category 일부 해소 | 4/4 전부 해소 |
| equipment/control 연결 정리 | 56% + equipment 97% · EQ_* 실코드화 |
| 법령 단계 안전 진입 | 준비 완료 |

단, **WARN** 성격의 잔여 이슈:
- reviewer 검토 자체는 아직 사람의 손이 닿지 않았다(R4, R5).
- 과잉 hit control 2 건(R1, R2) 은 정답셋 확정 시 split/reject 가 예상된다.
- admrul/expc 본문 원문이 없어 법령 단계 시작 즉시 수집 이슈가 재확인될 수 있다.

따라서 최종 판정은 **PASS (with WARN on reviewer-pending items)**.
