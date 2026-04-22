# 문장 상세 분류 스키마 (v0.1)

> 목적: 위험성평가 엔진이 문서(법·규칙·고시·KOSHA·해석례)에서
> "조건 → 의무/금지/조치" 구조를 뽑을 수 있도록, 문장 단위 라벨 체계를 고정한다.
> 본 문서는 **설계 초안**이며, 샘플 라벨링(CSV) → 규칙 검증 → 반자동 분류 → 전량 적용 순서로 진화한다.

---

## 1. 설계 원칙

1. 문장 검색용 태그가 아닌 **판단 엔진용 구조**를 만든다.
2. 하나의 문장은 여러 축(sentence_type, obligation, subject, action, condition, evidence)에서 동시에 분류될 수 있다.
3. 기존 master(`hazards`, `work_types`, `equipment`) 와 **호환 가능한 candidate 필드**를 둔다.
4. 단일 키워드로 확정 가능한 경우와 문맥 판단이 필요한 경우를 **규칙 문서에서 구분 표기**한다.
5. MSDS 상투 문장 등은 `descriptive_noise` 로 별도 분리해 엔진 입력에서 제외한다.

---

## 2. 분류 축(6)

### 2.1 sentence_type — 문장 구조 유형

| 코드 | 한글 | 판정 기준 | 키워드/패턴 | 포함 예 | 제외 예 |
|------|-----|----------|------------|--------|---------|
| `requirement` | 의무 | "…여야 한다", "설치/비치/배치하여야" 조동사 결합 | `하여야 한다`, `해야 한다`, `비치하여야`, `설치하여야`, `갖추어야` | "사업주는 안전난간을 설치하여야 한다." | "설비 특성을 고려한다."(단순 설명) |
| `prohibition` | 금지 | 부정·금지 표현 | `해서는 아니 된다`, `금지한다`, `사용하여서는 안`, `출입하지 아니하도록` | "인화성 물질 주변에서 화기 작업을 해서는 아니 된다." | 부정 없는 권고 |
| `caution` | 주의 | 약한 의무·권고 | `주의`, `유의`, `조심`, `신중히` | "고소작업 시 추락에 주의한다." | `requirement` 로 판정 가능한 강제문 |
| `procedure` | 절차 | 순서/단계/방법 설명 | `작업 순서`, `다음 순서`, `작업방법`, `첫째/둘째` | "굴착작업 순서는 ① 표토 제거 …" | 단일 항목만 있는 의무문 |
| `condition_trigger` | 조건 | 조건절 우세 | `~인 경우`, `~이상`, `~시`, `~할 때` | "높이 2m 이상의 작업발판 위에서 작업하는 경우" | 조건절이 전체 문장의 보조 역할 |
| `equipment_rule` | 장비 규칙 | 특정 장비/설비 대상 의무/금지/점검 | `안전난간`, `방호장치`, `비계`, `크레인`, `이동식` | "크레인의 과부하방지장치는 매일 점검한다." | 장비명만 언급된 설명문 |
| `ppe_rule` | 보호구 규칙 | PPE 관련 지급/착용/관리 | `보호구`, `안전모`, `안전대`, `호흡보호구`, `내화학장갑` | "근로자에게 안전대를 지급하고 착용시켜야 한다." | 일반 "안전" 키워드만 있는 경우 |
| `inspection_rule` | 점검·측정 | 정기·상시 점검/측정/확인 | `점검하여야`, `측정`, `확인`, `검사`, `주기` | "작업환경측정은 6개월마다 실시하여야 한다." | 단발성 확인 문장 |
| `education_rule` | 교육 | 교육/훈련 의무 | `교육`, `특별교육`, `안전교육`, `이수`, `훈련` | "근로자에게 특별안전보건교육을 실시하여야 한다." | 자료·매뉴얼 단순 안내 |
| `document_rule` | 서류 | 작성/게시/비치/보존 | `작성`, `게시`, `비치`, `보존`, `기록`, `MSDS` | "안전보건관리규정을 작성·게시하여야 한다." | 단순 참고문헌 |
| `emergency_rule` | 비상·응급 | 비상조치/대피/응급 | `비상`, `대피`, `응급`, `구조`, `피난` | "화재 발생 시 대피 경로를 확보하여야 한다." | 단순 비상구 언급 |
| `legal_reference` | 법령참조 | 다른 조항/별표/고시 참조 | `제○○조`, `별표`, `고시 제`, `같은 법` | "산업안전보건법 제29조에 따라 실시한다." | 본문 실체 규정 |
| `scope_exclusion` | 제외·예외 | 적용 제외 범위 | `제외한다`, `적용하지 아니한다`, `다만`, `예외` | "다만, 50인 미만 사업장은 제외한다." | — |
| `definition` | 정의 | 용어 정의 | `"○○"이란 …을 말한다`, `의미한다`, `정의한다` | "'밀폐공간'이란 산소결핍… 공간을 말한다." | — |
| `descriptive_noise` | 설명·노이즈 | MSDS·일반 설명·배경 | `참고`, `정보`, `특성`, `경우가 있다`, `사용된다` | "해당 물질은 황색 액체이다." | 의무와 결합된 설명 |

### 2.2 obligation_level — 의무 강도

| 코드 | 한글 | 기준 |
|------|-----|------|
| `mandatory` | 강제 | "하여야 한다"·"해야 한다" 결합 |
| `prohibited` | 금지 | "해서는 안 된다"·"금지" |
| `recommended` | 권장 | "하도록 권고", "할 수 있다" |
| `cautionary` | 주의 | "주의", "유의" |
| `informative` | 정보 | 설명문, 정의문 |
| `exception` | 예외 | "다만", "제외한다" |

### 2.3 subject_type — 문장의 주체

| 코드 | 한글 |
|------|-----|
| `employer` | 사업주 |
| `manager` | 관리자 |
| `supervisor` | 작업지휘자·관리감독자 |
| `safety_manager` | 안전관리자·보건관리자 |
| `worker` | 근로자 |
| `contractor` | 도급인·수급인 |
| `equipment` | 장비·설비 그 자체 |
| `workplace` | 사업장·작업장소 |
| `chemical` | 유해·위험물질 |
| `document` | 서류·기록 |
| `mixed_or_unknown` | 복합/불명 |

### 2.4 action_type — 요구되는 행위

| 코드 | 한글 |
|------|-----|
| `install` | 설치 |
| `inspect` | 점검 |
| `measure` | 측정 |
| `wear` | 착용 |
| `provide` | 지급·비치 |
| `train` | 교육 |
| `post` | 게시 |
| `prepare` | 작성·준비 |
| `record` | 기록 |
| `report` | 보고·신고 |
| `isolate` | 격리·차단 |
| `ventilate` | 환기 |
| `clean` | 청소·제거 |
| `store` | 보관·저장 |
| `prohibit_access` | 출입금지 |
| `monitor` | 감시·모니터링 |
| `maintain` | 유지·정비 |
| `mixed_or_unknown` | 복합/불명 |

### 2.5 condition_type — 발동 조건

| 코드 | 한글 | 예시 |
|------|-----|------|
| `quantity_threshold` | 수량·규모 | "50인 이상", "5톤 이상" |
| `equipment_presence` | 특정 장비 존재 | "크레인을 사용하는 경우" |
| `hazardous_substance` | 유해물질 | "관리대상 유해물질", "특별관리물질" |
| `confined_space` | 밀폐공간 | "밀폐공간에서 작업" |
| `height_work` | 고소 | "높이 2m 이상" |
| `lifting_operation` | 양중 | "양중작업", "인양" |
| `electrical_work` | 전기 | "충전전로", "활선" |
| `hot_work` | 화기 | "용접·용단·화기" |
| `weather_environment` | 기상·환경 | "강풍", "폭염", "우천" |
| `simultaneous_work` | 동시작업 | "복수 사업주", "혼재작업" |
| `periodic_schedule` | 주기 | "매일", "6개월마다" |
| `before_after_work` | 작업전/후 | "작업 시작 전" |
| `incident_emergency` | 사고·비상 | "재해 발생 시" |
| `legal_scope` | 법적 적용범위 | "상시근로자 수 ○○명 이상" |
| `none_or_unknown` | 조건 없음/불명 | — |

### 2.6 evidence_type — 출처 유형

| 코드 | 한글 | 비고 |
|------|-----|------|
| `law` | 법 (산안법 등) | `documents.source_type='law'` |
| `admrul` | 행정규칙 | `source_type='admrul'` |
| `licbyl` | 별표 | `source_type='licbyl'` |
| `expc` | 해석례 | `source_type='expc'` |
| `kosha` | KOSHA 자료 | `source_type='kosha'` |
| `internal_rule` | 사내규정 | 향후 확장 |
| `unknown` | — | — |

---

## 3. 스키마-기존 master 연결 방침

- `work_type_candidate`, `hazard_candidate`, `equipment_candidate` 컬럼은 기존 master 의 `*_code` 를 재사용.
- 기존 master 없음 → `null` 허용, reviewer 가 검토 후 master 보강 여부 결정.
- 법령 근거는 기존 `document_law_map(match_type='article')` 로 링크 가능(같은 법조문 doc id).
- 조치 master(`controls`) 는 **미존재 — 향후 별도 설계 필요 (섹션 8 참고)**.

---

## 4. MSDS / 일반 noise 문장 분리 규칙

아래 패턴이 **단독**으로 나타나고 의무·금지·조건 신호가 없는 경우 `descriptive_noise` 로 분류한다.

| 패턴 유형 | 예시 |
|-----------|------|
| 물성 설명 | "황색 액체이다", "끓는점은 ○○이다" |
| MSDS 상투 | "경고표지를 부착하여야 한다"(✗ 이건 `document_rule`) / "피부에 접촉하면 증상이 나타날 수 있다" |
| 반복 문구 | "MSDS 를 참고하세요", "자세한 내용은 별지 참조" |
| 일반 배경 | "산업안전은 중요하다", "근로자의 안전을 위하여" (단독) |
| 참고 문서 안내 | "OPL 참고", "교육미디어 확인" |

**중요**: 아래 신호 중 하나라도 결합되면 noise 가 아니라 각 rule 타입으로 재분류한다.
- 보호구 지급/착용 (`ppe_rule`)
- 환기·국소배기 (`equipment_rule` + action=`ventilate`)
- 저장·보관 (`equipment_rule` + action=`store`)
- 폭발성·독성 + 조건 임계값 (`condition_trigger` + `hazardous_substance`)
- 측정 의무 (`inspection_rule` + action=`measure`)

---

## 5. 애매한 경우 처리

1. **여러 sentence_type 후보 결합**: 1순위 라벨만 채우고 reviewer_note 에 2순위 기록.
2. **의무 강도 애매**: 일단 `informative` 로 두고 reviewer 확정.
3. **subject 불명**: `mixed_or_unknown` 채우고 노트.
4. **조건·결과 혼재 문장**: `condition_trigger` 1순위, result 부분은 별 sample 로 분리(후속 단계).

---

## 6. 버전 정책

- 파일 버전: `v0.1` (초안).
- 축 추가/변경 시 반드시 이 문서부터 갱신.
- 라벨링 CSV 의 `schema_version` 컬럼에 실제 사용한 버전 기록.
