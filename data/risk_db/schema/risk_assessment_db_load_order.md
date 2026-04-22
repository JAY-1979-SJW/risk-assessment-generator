# 위험성평가표 DB 적재 순서 (v1.0 초안)

- 대상 DBMS : PostgreSQL 14+
- 작성일   : 2026-04-22
- 적용 DDL : `risk_assessment_db_schema.sql`
- 주의     : 본 문서는 **설계 초안**이며 실제 마이그레이션/적재는 본 단계에서 수행하지 않는다.

---

## 권장 적재 순서

```
1. hazards
2. work_types
3. equipment
4. documents
5. kosha_meta / law_meta / expc_meta      -- documents.id 기반 1:1
6. document_hazard_map
7. document_work_type_map
8. document_equipment_map
9. risk_assessment_results   (선택, 캐시성)
10. collection_runs / normalization_runs  (운영 이력)
```

---

## 왜 이 순서인가

- **FK 의존성 해소** 가 1차 기준이다.
  - `document_*_map` 3개 테이블은 `documents`, `hazards`, `work_types`, `equipment` 가 먼저 존재해야 INSERT 가능.
  - `kosha_meta` / `law_meta` / `expc_meta` 는 `documents.id` 를 PK 로 재사용하므로 `documents` 가 먼저 있어야 한다.
- **표준 코드가 우선** 이다.
  - `hazards / work_types / equipment` 는 정답지(마스터) 역할.
  - normalized JSON 의 배열 값은 여기 등록된 코드에만 매핑되어야 한다.
  - 마스터가 먼저 있어야 `document_*_map` 입력 시 FK 실패가 없다.
- **1:1 메타는 본체 직후** 에 적재.
  - `documents` INSERT → 해당 row 의 `id` 로 즉시 `*_meta` 를 INSERT 해야 정합성이 유지된다.
  - 트랜잭션으로 묶으면 좋다.
- **N:M 매핑은 가장 마지막**.
  - 본체/마스터가 모두 있어야 성립.
- **`risk_assessment_results`, `*_runs`** 는 운영/감사 성격이라 순서 상관이 없지만,
  본체 적재가 끝난 뒤에 쌓이기 시작하므로 마지막에 둔다.

---

## unique 충돌 처리 원칙

### documents
- 유니크 키 : `(source_type, source_id)`
- 재수집 시 처리 : **UPSERT (INSERT ... ON CONFLICT)**
  ```sql
  INSERT INTO documents (source_type, source_id, title, ...)
  VALUES (...)
  ON CONFLICT (source_type, source_id) DO UPDATE
  SET title = EXCLUDED.title,
      title_normalized = EXCLUDED.title_normalized,
      body_text = EXCLUDED.body_text,
      has_text = EXCLUDED.has_text,
      content_length = EXCLUDED.content_length,
      url = EXCLUDED.url,
      file_url = EXCLUDED.file_url,
      pdf_path = EXCLUDED.pdf_path,
      file_sha256 = EXCLUDED.file_sha256,
      language = EXCLUDED.language,
      status = EXCLUDED.status,
      published_at = EXCLUDED.published_at,
      collected_at = EXCLUDED.collected_at,
      updated_at = now();
  ```

### hazards / work_types / equipment
- 유니크 키 : `*_code` (PK), `*_name` (UNIQUE)
- **마스터성 테이블**이므로 신규 코드가 나타났을 때만 INSERT.
- 기존 코드가 있으면 `ON CONFLICT DO NOTHING` 을 원칙으로 한다.
  이름 변경은 별도 관리 프로세스를 통해 수동 승인 후 UPDATE.

### document_*_map
- PK : `(document_id, *_code)`
- **전체 재계산 전략** 권장:
  1. 해당 `document_id` 의 매핑을 먼저 DELETE.
  2. 최신 매핑 배열을 전부 INSERT.
- 이유 : 매핑은 normalize 단계의 AI/규칙 결과이고, 다시 돌리면 변동될 수 있다.
  부분 UPSERT 보다 **삭제 후 재삽입** 이 의미가 명확하다.

### *_meta (1:1)
- PK : `document_id`
- `ON CONFLICT (document_id) DO UPDATE` 로 덮어쓴다.
- 이유 : 정규화 재실행 시 메타 필드가 갱신될 수 있다.

### collection_runs / normalization_runs
- **append-only** 로그 테이블.
- 유니크 제약이 없으므로 매 실행마다 신규 row 로 쌓는다.

### risk_assessment_results
- append-only 캐시 성격.
- 동일 query 재질의가 들어와도 **새 row 로 기록**한다.
  (과거 결과 비교 및 감사 목적)

---

## 재수집 / 재정규화 시 upsert 기준

| 단계 | 대상 | 기준 키 | 전략 |
|---|---|---|---|
| 재수집 후 documents 갱신 | documents | (source_type, source_id) | UPSERT, updated_at=now() |
| 표준 코드 신규 발견 | hazards/work_types/equipment | *_code | INSERT ... ON CONFLICT DO NOTHING |
| 정규화 재실행 - 매핑 | document_*_map | document_id | DELETE + 일괄 INSERT |
| 정규화 재실행 - 메타 | kosha_meta/law_meta/expc_meta | document_id | UPSERT |
| 위험성평가 재생성 | risk_assessment_results | — | append-only (새 row) |
| 실행 이력 | collection_runs / normalization_runs | — | append-only (새 row) |

---

## source_type + source_id 를 기준키로 보는 이유

- **원천 시스템이 서로 다르다.**
  - KOSHA `medSeq`, 국가법령 `law_id`, 해석례 `expc_id` 는 서로 독립 네임스페이스.
  - `(source_type, source_id)` 로 묶어야 전역 유일성이 보장된다.
- **재수집에 강하다.**
  - 원천 시스템의 고유 ID 는 원칙적으로 변하지 않는다.
  - 제목·URL 변경이 있어도 이 키가 있으면 기존 row 를 안전하게 덮어쓸 수 있다.
- **향후 video / osha 등 신규 소스 추가 시**
  `source_type` 값만 늘리면 같은 규칙이 그대로 적용된다.

---

## file_sha256 의 사용 목적

- **내용 기반 중복 판정** 용도.
  - 같은 `source_id` 에 다른 PDF 가 올라올 수 있고 (재공지/개정판),
  - 다른 `source_id` 에 동일 PDF 가 중복 등록될 수도 있다.
  - SHA-256 해시를 비교하면 이 두 경우 모두를 감지할 수 있다.
- **스토리지 절감 / 재다운로드 방지**
  - 해시가 동일하면 이미 가지고 있는 원본을 재다운로드하지 않는다.
  - `pdf_path` 재사용 여부 판단 기준이 된다.
- **감사/추적**
  - 본문 텍스트만 비교하면 OCR/정규화 차이로 인해 오탐이 생긴다.
  - 원본 바이너리 해시는 명확한 증거가 된다.
- `documents(file_sha256)` 인덱스가 있으므로 중복 여부를 O(log n) 으로 조회할 수 있다.
- **주의** : 해시는 **중복 감지용 참고값**이지 기준키는 아니다.
  같은 해시라도 source_type/source_id 가 다르면 서로 다른 document row 로 유지한다.

---

## 트랜잭션 단위 권장

- 문서 단위(document + *_meta + document_*_map) 는 **하나의 트랜잭션** 으로 묶는다.
- 표준 코드 마스터 갱신은 별도 트랜잭션으로 먼저 수행.
- 대량 적재 시에는 1,000 ~ 5,000 건 단위로 커밋해 lock 시간을 최소화한다.

---

## 본 문서가 다루지 않는 것

- 실제 적재 스크립트, 커넥션/튜닝 값.
- trigger / function / enum / 전문검색 인덱스 생성.
- 이관 스케줄, 운영 환경 분리, 백업 전략.
- 위 항목은 다음 단계(마이그레이션 실행 설계)에서 별도 문서로 다룬다.
