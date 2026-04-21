# law raw 정규화 규칙

작성일: 2026-04-21  
단계: 2단계 — raw staging 정규화 및 기준 법령 DB 초안 생성

---

## 입력 raw 파일

| 파일 | target | category | 비고 |
|------|--------|----------|------|
| `law_raw/laws_index.json` | `law` | statute | 법·시행령·시행규칙 |
| `law_raw/admin_rules_index.json` | `admrul` | admin_rule | 고시·예규·훈령 |
| `law_raw/licbyl_index.json` | `licbyl` | licbyl | 별표·서식 |
| `law_raw/expc_index.json` | `expc` | interpretation | 법령해석례 |

원본 raw 파일은 **읽기 전용**. 스크립트에서 절대 수정하지 않는다.

---

## source별 필드 매핑 규칙

### statute (target=law)
| 공통 스키마 필드 | raw 필드 |
|----------------|---------|
| `raw_id` | `법령일련번호` |
| `title_ko` | `법령명한글` |
| `title_short` | `법령약칭명` |
| `document_type` / `law_type` | `법령구분명` |
| `ministry_name` / `authority` | `소관부처명` |
| `promulgation_date` | `공포일자` |
| `enforcement_date` | `시행일자` |
| `revision_type` | `제개정구분명` |
| `status_text` | `현행연혁코드` |
| `reference_no` | `공포번호` |
| `detail_link` | `법령상세링크` |

### admin_rule (target=admrul)
| 공통 스키마 필드 | raw 필드 |
|----------------|---------|
| `raw_id` | `행정규칙일련번호` |
| `title_ko` | `행정규칙명` |
| `document_type` / `law_type` | `행정규칙종류` |
| `ministry_name` / `authority` | `소관부처명` |
| `promulgation_date` | `발령일자` |
| `enforcement_date` | `시행일자` |
| `revision_type` | `제개정구분명` |
| `status_text` | `현행연혁구분` |
| `reference_no` | `발령번호` |
| `detail_link` | `행정규칙상세링크` |

### licbyl (target=licbyl)
| 공통 스키마 필드 | raw 필드 |
|----------------|---------|
| `raw_id` | `별표일련번호` |
| `title_ko` | `별표명` |
| `document_type` | `별표종류` |
| `law_type` | `법령종류` |
| `ministry_name` / `authority` | `소관부처명` |
| `promulgation_date` | `공포일자` |
| `revision_type` | `제개정구분명` |
| `reference_no` | `공포번호` |
| `related_law_id` | `관련법령ID` |
| `related_law_name` | `관련법령명` |
| `detail_link` | `별표법령상세링크` |
| `file_link` | `별표서식파일링크` |
| `pdf_link` | `별표서식PDF파일링크` |

### interpretation (target=expc)
| 공통 스키마 필드 | raw 필드 |
|----------------|---------|
| `raw_id` | `법령해석례일련번호` |
| `title_ko` | `안건명` |
| `reference_no` | `안건번호` |
| `authority` | `질의기관명→회신기관명` 조합 |
| `ministry_name` | `회신기관명` |
| `promulgation_date` | `회신일자` |
| `document_type` / `law_type` | 고정값 `해석례` |
| `detail_link` | `법령해석례상세링크` |

---

## 날짜 정규화 규칙

모든 날짜 필드는 `YYYY-MM-DD`로 변환한다.

| 입력 형식 | 변환 결과 |
|----------|---------|
| `20210518` | `2021-05-18` |
| `2005.12.23` | `2005-12-23` |
| `2021-05-18` | 그대로 유지 |
| 빈값 | 빈값 유지 |
| 기타 | 빈값 + reject 사유 기록 |

원문은 `raw_payload`에 항상 보존된다.

---

## 링크 절대경로 정규화 규칙

상대경로 → `https://www.law.go.kr` 앞에 붙임.

| 입력 | 변환 결과 |
|------|---------|
| `/DRF/lawService.do?...` | `https://www.law.go.kr/DRF/lawService.do?...` |
| `/LSW/flDownload.do?...` | `https://www.law.go.kr/LSW/flDownload.do?...` |
| 빈값 | 빈값 유지 |
| `http://...` 이미 절대경로 | 그대로 유지 |

---

## dedupe 기준

| 우선순위 | key |
|---------|-----|
| primary | `category + raw_id` |
| secondary | `category + title_ko + reference_no` (raw_id 없을 때) |

- 동일 key 충돌 시 먼저 처리된 항목 유지, 나머지 reject (reason=`duplicate`)
- 원본 raw 파일은 수정하지 않음

---

## reject 기준

| reason | 조건 |
|--------|------|
| `empty_item` | item이 비었거나 유효 필드 없음 |
| `missing_raw_id` | raw_id 추출 실패 |
| `missing_title` | title_ko 추출 실패 |
| `duplicate` | 동일 dedupe key 재등장 |
| `invalid_date` | 날짜 변환 실패 (원문 있음) |
| `mapping_error` | 매퍼 실행 예외 |

---

## 산출물

| 파일 | 설명 |
|------|------|
| `law_normalized/safety_laws_normalized.json` | 정규화 성공 항목 (기준 DB 초안) |
| `law_normalized/safety_laws_rejects.json` | 정규화 실패·제외 항목 |

`safety_laws_normalized.json`은 아직 운영 DB가 아닌 **기준 DB 초안**이다.

---

## 다음 단계에서 할 일

- `DATA_GO_KR_SERVICE_KEY` 설정 후 실 수집 재실행
- 정규화 항목에 `law_hazard_map` 연결 (별도 단계)
- 기존 `safety_laws.json` 수동 항목과 병합 검토 (별도 단계)

## 다음 단계에서 하지 말 것

- 이 파일을 DB에 직접 insert 하지 말 것
- `law_hazard_map`, `law_worktype_map`, `law_control_map` 생성하지 말 것
- KOSHA 데이터와 자동 병합하지 말 것
- 엔진·UI 수정하지 말 것
