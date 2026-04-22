# controls master 설계 초안 (v0.1)

> 목적: 위험성평가표의 "감소대책/안전조치" 컬럼을 자동화하기 위한
> 재사용 가능한 **표준 대책(control) 마스터** 체계를 정의한다.
> 본 문서는 **초안**이며 운영 DB 반영은 **후속 단계**에서 결정한다.

---

## 1. 설계 원칙

1. 현장 실무에서 그대로 쓰이는 "표준 대책 단위"로 만든다 — 문장 원문 복붙 금지.
2. 하나의 사고 시나리오는 여러 control 을 동시에 요구할 수 있다 (`1 sentence : N controls`).
3. **control ≠ hazard ≠ condition**. 결과물(대책)만 담는다.
4. 기존 master(`hazards`·`work_types`·`equipment`) 를 FK 로 재사용.
5. 위계 없이 flat code 구조 + `control_category` / `control_type` 2축 분류.

---

## 2. 분류 체계

### 2.1 control_category (대분류 · 12종)

| 코드 | 한글 | 설명 |
|------|-----|------|
| `engineering_control` | 공학적 대책 | 설비·물리적 방호·차단·환기·추락방지·가드 |
| `administrative_control` | 관리적 대책 | 작업계획·출입통제·절차 운영·표지 |
| `ppe_control` | 보호구 | 지급·착용·교체·관리 |
| `training_control` | 교육 | 특별교육·작업 전 교육·TBM·주지 |
| `inspection_control` | 점검·측정 | 정기·상시 점검, 작업환경측정, 체크리스트 |
| `document_control` | 문서 | 작성·비치·게시·보존·기록 |
| `emergency_control` | 비상·응급 | 대피·응급조치·비상연락·구조체계 |
| `health_control` | 건강관리 | 유해노출 관리·건강진단·작업환경 개선 |
| `housekeeping_control` | 정리정돈 | 적치·청소·통로·미끄럼 방지 |
| `supervision_control` | 감독·감시 | 관리감독자·신호수·감시인·입회 |
| `permit_control` | 작업허가 | 작업허가서·밀폐공간 허가·화기허가 |
| `traffic_control` | 교통·동선 | 중장비 동선·유도·충돌방지·작업구역 분리 |

### 2.2 control_type (표준 대책 세부 유형)

- category 하위의 재사용 가능한 표준 코드. 직접적인 문장 1회성 사용 금지.
- 예: `fall_protection_install`, `local_ventilation_install`, `ppe_wear`, `periodic_inspection`, `pre_work_briefing` 등.
- 상세 리스트는 `data/risk_db/master/controls_master_draft.csv` 참조.

---

## 3. controls master 스키마 (파일 기반 초안)

| 컬럼 | 타입 | 설명 |
|------|-----|------|
| `control_code` | text | PK. slug 형 (예: `ctrl_fall_protection_install`) |
| `control_name_ko` | text | 한글 대책명 (렌더링 기본값) |
| `control_name_en` | text | 영문 라벨 |
| `control_category` | text | 12종 중 1 |
| `control_type` | text | 표준 type 슬러그 |
| `description` | text | 대책의 구체 설명 (1~2문) |
| `typical_keywords` | text | 파이프 구분 (예: `안전난간\|안전난간대\|가드`) |
| `typical_verbs` | text | 파이프 구분 (예: `설치\|부착\|고정`) |
| `related_sentence_types` | text | sentence 스키마 라벨, 콤마 구분 |
| `related_hazard_codes` | text | `hazards.hazard_code` FK, 콤마 구분 |
| `related_equipment_codes` | text | `equipment.equipment_code` FK, 콤마 구분 |
| `related_work_type_codes` | text | `work_types.work_type_code` FK, 콤마 구분 |
| `legal_required_possible` | text | `Y` / `N` — 법적 근거 문장 매칭 가능성 |
| `review_status` | text | `draft` / `reviewed` / `deprecated` |
| `note` | text | 리뷰어 메모 |

---

## 4. 자연어 렌더링 규칙 초안

control 레코드를 위험성평가표 "감소대책" 컬럼에 풀어쓸 때의 **기본 템플릿**.

| control_type | 한글 렌더링 예 |
|-----|-----|
| `ctrl_fall_protection_install` | "작업발판·안전난간·개구부 덮개 등 추락방지 설비를 설치하고 상태를 확인한다" |
| `ctrl_local_ventilation_install` | "국소배기장치를 설치·운전하고 성능을 확인한다" |
| `ctrl_guard_installation` | "회전·절단부에 방호장치를 설치하고 탈착 여부를 점검한다" |
| `ctrl_lockout_tagout` | "정비·청소 시 기동장치를 잠그고 'LOTO 표지'를 부착한다" |
| `ctrl_ppe_wear` | "해당 작업에 적합한 보호구(안전모·안전대·보안경 등)를 착용한다" |
| `ctrl_ppe_provision` | "작업에 적합한 보호구를 근로자에게 지급하고 교체 주기를 관리한다" |
| `ctrl_special_training` | "해당 작업 근로자에게 특별안전보건교육을 실시한다" |
| `ctrl_pre_work_briefing` | "작업 전 위험요인·작업순서·보호구를 주지(TBM)한다" |
| `ctrl_periodic_inspection` | "설비의 방호장치·과부하장치 등을 정기적으로 점검한다" |
| `ctrl_atmospheric_measurement` | "밀폐공간 작업 전 산소·유해가스 농도를 측정한다" |
| `ctrl_checklist_verification` | "표준 점검표로 작업 전·중 상태를 점검·기록한다" |
| `ctrl_msds_posting` | "취급 물질의 MSDS·경고표지를 게시하고 비치한다" |
| `ctrl_record_retention` | "점검·교육·측정 기록을 법정 기간 보존한다" |
| `ctrl_emergency_evacuation` | "비상 시 대피 경로·집결지·연락체계를 수립·주지한다" |
| `ctrl_fire_watch_assignment` | "화기작업 중 화재감시인을 배치하고 작업 후 30분 이상 잔류한다" |
| `ctrl_standby_person_assignment` | "밀폐공간 등 고위험 작업 외부에 감시인을 상시 배치한다" |
| `ctrl_housekeeping_cleanup` | "작업장·통로의 자재 적치, 누유·분진을 정리한다" |
| `ctrl_traffic_guide_assignment` | "중장비·차량 이동 구간에 신호수·유도자를 배치한다" |
| `ctrl_access_restriction` | "위험구역 출입금지 표지·차단 설비를 설치하고 관계자 외 접근을 통제한다" |
| `ctrl_work_permit_issue` | "해당 작업에 대해 작업허가서를 발행하고 승인 후 착수한다" |

---

## 5. 애매한 경우 처리 규칙

| 케이스 | 처리 |
|--------|------|
| 동일 의미 여러 표현 | 같은 `control_code` 로 묶고 `typical_keywords` alias 추가 |
| category 경계 애매 | `control_category` 는 1개만 — `note` 에 2순위 기록 |
| hazard 와 혼동 | control 에 넣지 않음. hazard candidate 로만 유지 |
| condition 과 혼동 | control 에 넣지 않음. condition_type 로 유지 |
| 일회성 특수 조치 | master 에 넣지 않고 `sentence → free_text` 로 처리 |

---

## 6. 운영 반영 전제

- 이 문서는 **초안**. 실제 DB 테이블 생성·쿼리 추가·API 변경은 **다음 단계**.
- reviewer 검토 후 정답셋 확정 → SQL DDL 작성 → 반자동 매핑기 → 단계적 반영.

---

## 7. 버전

- v0.1 (초안) · 400 문장 샘플 + 기존 master(14·22·18) 기반.
- 축 추가 시 반드시 본 문서 갱신 + CSV `schema_version` 갱신.
