# Excel Builder Scaffold — 신규 안전서류 builder 작성 가이드

## 목적

`engine/output/_excel_builder_scaffold_template.py`를 복사 기반으로 신규 안전서류 Excel builder를
일관된 구조와 공통 helper로 빠르게 작성하기 위한 절차 문서이다.

scaffold 파일 자체는 `form_registry`에 등록되지 않으며, production 코드에서 import하지 않는다.

---

## 신규 builder 작성 순서

```
1. document_catalog.yml에서 구현 대상 문서 확인
2. scaffold 복사
3. 파일/함수/상수 수정 (아래 "반드시 바꿀 항목" 참조)
4. py_compile 통과 확인
5. form_registry.py에 FormSpec 1건 추가
6. document_catalog.yml 해당 문서 DONE 갱신
7. 검증 명령어 실행
8. 커밋
```

---

## 복사 명령

```bash
cp engine/output/_excel_builder_scaffold_template.py \
   engine/output/{form_name}_builder.py
```

---

## 복사 후 반드시 바꿀 항목

### 1. 파일명
```
engine/output/{form_name}_builder.py
```
명명 규칙: `{대상}_builder.py` (소문자, 언더스코어)
예: `confined_space_workplan_builder.py`, `piling_workplan_builder.py`

### 2. build 함수명
```python
# 변경 전
def build_standard_excel(form_data, ...) -> bytes:

# 변경 후
def build_{form_name}_excel(form_data, ...) -> bytes:
```

### 3. 문서 메타데이터 상수
```python
DOC_ID         = "XX-000"         # → 예: "WP-003", "EQ-009"
FORM_TYPE      = "standard_form"  # → form_registry와 일치
SHEET_NAME     = "표준서식"        # → 31자 이하, xlsx sheet 탭명
SHEET_HEADING  = "표준 안전서류"   # → 서식 표제 (셀 A1)
SHEET_SUBTITLE = "..."             # → 법령 근거 문구
```

### 4. section labels (한국어 라벨)
각 `_write_*` 함수 내 `_lv(ws, row, "라벨명", ...)` 호출의 라벨 문자열을
서식 특성에 맞게 수정한다.

### 5. 반복 테이블 max/min 행 수
```python
MAX_CHECKLIST_ROWS = 10   # → 서식에 맞게 조정
MIN_CHECKLIST_ROWS = 5
MAX_HAZARD_ROWS    = 10
MIN_HAZARD_ROWS    = 5
```

### 6. form_data key
각 `v(data, "key_name")` 호출의 key 문자열을 form_data 실제 필드명으로 변경한다.
`required_fields`에 포함될 필드는 `None` 입력 시 API가 400을 반환하므로
builder 내에서 별도 필수 검증을 추가하지 않는다 (registry가 담당).

---

## registry 등록 방법

`engine/output/form_registry.py`에 아래 항목을 추가한다.

### 1. import 1줄 추가
```python
from engine.output.{form_name}_builder import build_{form_name}_excel
```

### 2. docstring 목록에 1줄 추가
```
    {form_type}  — {display_name} (v1.0)  [{DOC_ID}]
```

### 3. `_REGISTRY` dict 끝 `}` 바로 앞에 FormSpec 1건 추가
```python
    "{form_type}": FormSpec(
        form_type="{form_type}",
        display_name="{서식 표시명}",
        version="1.0",
        builder=build_{form_name}_excel,
        required_fields=(
            # 법령 근거: {조항}
            "field_a",
            "field_b",
        ),
        optional_fields=(
            "site_name",
            "project_name",
            # ... 나머지 선택 필드
        ),
        repeat_field="{hazard_items or None}",
        max_repeat_rows=10,          # None이면 생략 가능
    ),
```

규칙:
- `required_fields`에는 법령이 명시한 필수 항목만 포함
- `optional_fields`에는 관행적 항목 포함
- `extra_list_fields`는 `list[str]` 또는 `list[dict]`인 2차 목록 필드에만 사용
- 기존 FormSpec 수정 금지

---

## catalog 갱신 방법

`data/masters/safety/documents/document_catalog.yml`에서
해당 `id` 블록만 수정한다.

```yaml
  - id: {DOC_ID}
    name: {서식명}
    # ... (기존 필드 유지)
    implementation_status: DONE   # ← TODO → DONE
    priority: DONE                # ← P1/P2 등 → DONE
    form_type: {form_type}        # ← null → 실제 form_type
    notes: "builder v1.0. ..."    # ← null → 간략 설명
```

규칙:
- 해당 문서 1건만 수정
- 다른 문서 수정 금지
- `legal_basis`, `legal_status`, `evidence_id`, `evidence_file`은 임의 추가 금지
  (evidence 작업은 별도 evidence 생성 단계에서 수행)

---

## 검증 명령어

```bash
# 1. 문법 검사
python -m py_compile engine/output/{form_name}_builder.py

# 2. import 확인
python -c "from engine.output.{form_name}_builder import build_{form_name}_excel; print('OK')"

# 3. registry 조회 확인
python -c "
from engine.output.form_registry import get_form_spec
spec = get_form_spec('{form_type}')
print(spec['display_name'], spec['required_fields'])
"

# 4. xlsx 생성 + 재오픈 확인
python - <<'PY'
import tempfile, os
from openpyxl import load_workbook
from engine.output.form_registry import build_form_excel

xlsx = build_form_excel("{form_type}", {
    "required_field_a": "테스트값",
    "required_field_b": "테스트값",
})
with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as f:
    f.write(xlsx); tmp = f.name
wb = load_workbook(tmp); os.unlink(tmp)
print(f"OK: {len(xlsx):,} bytes, sheet={wb.active.title}")
PY
```

---

## 금지 사항

| 항목 | 이유 |
|------|------|
| 기존 builder 무단 수정 | smoke test 회귀 위험 |
| evidence 파일 임의 생성 | 법령 해석 필요, 별도 단계에서 수행 |
| 법령 근거 임의 판단 | 전문 영역, builder 코드에 포함하지 않음 |
| registry 다건 수정 | 1 PR = 1 form 원칙 |
| document_catalog.yml 다건 수정 | 검증 범위 최소화 |
| `legal_status`, `evidence_id` 임의 설정 | evidence 검증 후 별도 추가 |
| form_registry.py에 직접 로직 추가 | dispatcher 역할만 유지 |
| scaffold 파일 직접 registry 등록 | 복사 후 사용 원칙 |

---

## 최종 보고 형식 (커밋 전 자체 확인)

```
[선별 문서]
- document_id:
- 문서명:
- priority:
- 법정/실무:

[신규 builder]
- 파일명:
- 함수명:
- sheet title:
- helper 사용: write_cell ✓ / apply_col_widths ✓ / border_rect ✓ (최소 2개)

[검증]
- py_compile: OK
- import: OK
- registry spec 조회: OK
- xlsx 생성: OK (N bytes)
- load_workbook: OK

[git diff 범위]
- engine/output/{form_name}_builder.py
- engine/output/form_registry.py
- data/masters/safety/documents/document_catalog.yml

[커밋 메시지]
feat(safety): add shared-style Excel builder for {DOC_ID}
```
