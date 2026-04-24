# Export API 파일명 규칙 정의

**작성일**: 2026-04-24

---

## 1. 기본 규칙

```
{form_type}_{YYYYMMDD}_{HHMMSS}.xlsx
```

| 구성 요소 | 형식 | 설명 |
|---------|------|------|
| `{form_type}` | 소문자, 언더스코어 | registry form_type 식별자 그대로 사용 |
| `{YYYYMMDD}` | 8자리 날짜 | 생성 시점 날짜 (KST) |
| `{HHMMSS}` | 6자리 시각 | 생성 시점 시각 (KST, 24시간) |
| 확장자 | `.xlsx` | 항상 소문자 |

---

## 2. 예시

| form_type | 생성 시점 (KST) | 파일명 |
|-----------|--------------|------|
| `education_log` | 2026-04-24 15:30:22 | `education_log_20260424_153022.xlsx` |
| `excavation_workplan` | 2026-04-24 09:05:07 | `excavation_workplan_20260424_090507.xlsx` |

---

## 3. options.filename override

요청에 `options.filename`이 있으면 기본 규칙 대신 해당 값을 사용.

### 처리 규칙

| 조건 | 처리 |
|------|------|
| `options.filename` 없음 또는 `null` | 기본 규칙으로 자동 생성 |
| `options.filename` 있음 | 해당 값 사용 (정제 후) |
| `.xlsx` 미포함 | 자동으로 `.xlsx` 추가 |
| 경로 구분자(`/`, `\`, `..`) 포함 | 제거 후 사용 (경로 주입 방지) |
| 길이 255자 초과 | 255자로 잘라내고 `.xlsx` 붙임 |

### 정제 예시

| 입력 | 처리 결과 |
|------|---------|
| `"내_교육일지"` | `"내_교육일지.xlsx"` |
| `"report.xlsx"` | `"report.xlsx"` |
| `"../secret/file"` | `"..secretfile.xlsx"` (구분자 제거) |
| `"a" × 300` | `"a" × 251 + ".xlsx"` |

---

## 4. Content-Disposition 적용

```
Content-Disposition: attachment; filename="education_log_20260424_153022.xlsx"
```

- RFC 6266 준수
- 한글 파일명이 포함된 경우 RFC 5987 인코딩 적용:  
  ```
  Content-Disposition: attachment;
    filename*=UTF-8''%EC%95%88%EC%A0%84%EB%B3%B4%EA%B1%B4%EA%B5%90%EC%9C%A1%EC%9D%BC%EC%A7%80.xlsx
  ```

---

## 5. 시각 기준

| 항목 | 결정 |
|------|------|
| 타임존 | **KST (UTC+9)** — 보고서 생성일시는 항상 한국 표준시 |
| 취득 방법 | 서버 시각을 KST로 변환 (`datetime.now(ZoneInfo("Asia/Seoul"))`) |
| 동시 요청 충돌 | 초 단위 일치 가능 — 문제 없음 (파일은 클라이언트에 스트리밍, 서버 저장 없음) |
