# 수집기 write-flapping 방지 정책

**작성일**: 2026-04-23
**근거**: 서버 `/home/ubuntu/apps/risk-assessment-app/app` 의 git-guard FAIL.
`kosha_kosha_opl_*.json` 815 건이 Modified 로 반복 감지되었고, 내용 diff 는 `-/+` 쌍만 존재 (line ending 또는 trailing newline 만 바뀐 flapping).

본 문서는 **코드를 당장 수정하지 않는다**. 1순위 3개 대상과 적용할 유틸 형태만 확정하여, 이후 별도 PR 에서 교체한다.

---

## 1. 현상 (재정의)

수집기가 매번 **동일 데이터를 다시 저장**하면서 아래 요인 중 하나로 diff 발생:

| 요인 | 메커니즘 |
|------|----------|
| line ending 플래핑 | `Path.write_text()` 는 Python 의 text mode. Windows 에서 `\n` → `\r\n` 자동 치환. 서버(Linux) 는 `\n` 유지 → 실행 환경에 따라 CRLF/LF 가 교차 |
| trailing newline 유무 | JSON dump 후 마지막 `\n` 삽입 여부 통일 안 됨 → `\ No newline at end of file` 노이즈 |
| dict key 순서 | Python 3.7+ 는 insertion order 보존이지만, 수집 소스 순서가 미세하게 달라지면 key 순서도 변함 |
| floating point | `ensure_ascii=False` + 기본 repr → 같은 값이라도 반올림 표현이 다를 수 있음 (해당 데이터셋에서는 현재 영향 적음) |

`.gitattributes` 추가(`*.json text eol=lf`) 로 "1) line ending" 은 Git 레벨에서 해결되지만, **디스크의 실제 파일 내용** 은 수집기가 쓰는 대로 남으므로 "동일 데이터 재기록" 을 막으려면 아래 정책을 수집기 쪽에도 심어야 한다.

---

## 2. 공통 write 유틸 안

아래 함수를 `scripts/collect/_base.py` 에 추가하고, 향후 `save_json` 호출처를 이쪽으로 치환.

```python
import json
from pathlib import Path


def write_json_canonical(path: Path, data: dict, *, sort_keys: bool = True) -> bool:
    """
    same-bytes skip + LF + canonical JSON.

    반환값: True 면 실제 디스크 write 발생, False 면 no-op.
    """
    canonical = json.dumps(
        data,
        ensure_ascii=False,
        indent=2,
        sort_keys=sort_keys,
        separators=(",", ": "),
    ) + "\n"
    encoded = canonical.encode("utf-8")
    if path.exists() and path.read_bytes() == encoded:
        return False  # no-op: 바이트 수준 동일
    path.parent.mkdir(parents=True, exist_ok=True)
    # text mode 우회 → Windows 에서도 CRLF 변환 없음
    path.write_bytes(encoded)
    return True
```

### 2.1 설계 선택

- `sort_keys=True`: 수집 순서 영향을 제거. **단, 이미 커밋된 파일의 key 순서가 다르면 첫 실행에서 전면 rewrite 발생** → 의도된 1회성 flapping. 이 커밋은 수집기 교체 PR 에 포함되는 것이 자연스럽다.
- `indent=2`: 기존 정책 유지.
- `+ "\n"`: 마지막 개행 보장.
- `write_bytes`: text mode 우회. `\r\n` 치환 원천 차단.
- `read_bytes() == encoded`: 바이트 수준 비교. mtime 만 업데이트되고 내용 같은 경우 write 자체를 스킵 → git 에서도 변경 없음.

### 2.2 DO NOT

- `sort_keys=False` + 단순 skip 은 오히려 수집 소스 order 변동에 민감해 flapping 유발.
- `json.dumps(..., indent=2)` 만 바꾸고 `write_text` 유지 → CRLF 플래핑 방지 불가.

---

## 3. 1순위 3개 적용 대상

| 순위 | 파일 | 함수 | 영향 파일 수 | 영향 범위 |
|------|------|------|---------------|-----------|
| **1** | `scripts/collect/_base.py` | `save_json()` (L44~46) | — | 모든 `collect/*` 모듈(`admrul`, `expc`, `law`, `licbyl`, `moel_*` 등) 공유 → **가장 큰 레버리지**. 이 1개 교체 + 호출처는 `write_json_canonical` 별명으로 대체하거나 `save_json` 내부만 재작성 |
| **2** | `scripts/normalize/kosha_normalizer.py` | L161 `out_path.write_text(json.dumps(...))` (983 파일 쓰기) | 983 | `data/normalized/kosha/*.json` 의 flapping 차단. 서버 git-guard 가 Modified 로 잡던 대상 중 가장 큰 군 |
| **3** | `scripts/collect/kosha_guides.py` | `_save()` (L315~318, 내부는 `save_json`) | 983 | `data/raw/kosha/kosha_*.json` — OPL/교재 메타. 1번이 교체되면 자동 수혜이나 수집 주체가 가장 빈번히 재실행되므로 **명시적으로 언급**해 리뷰 대상에 포함 |

### 3.1 Follow-up (2순위, 본 목록 외)

- `scripts/normalize/expc_normalizer.py` L200
- `scripts/normalize/law_normalizer.py` L182
- `scripts/normalize/normalize_moel_expc.py` L44
- `scripts/normalize/normalize_law_raw.py` L363, L375
- `scripts/normalize/normalize_control_refs.py` L205/213/220

모두 동일 패턴 (`out_path.write_text(json.dumps(...), encoding="utf-8")`). 1번 교체 시 전수 치환 PR 로 묶는 것이 일관적.

---

## 4. 롤아웃 계획 (이후 PR)

1. `_base.py` 에 `write_json_canonical` 추가, `save_json` 을 얇은 래퍼(`return write_json_canonical(path, data)`)로 재작성.
2. normalize/* 의 직접 `out_path.write_text(json.dumps(...))` 를 `write_json_canonical(out_path, data)` 로 치환.
3. 최초 1회 전수 재저장 — sort_keys=True 적용으로 **key 순서 정렬 커밋 1건 발생 예상**. 이 커밋을 통해 이후 재수집은 "no-op 다수 + 진짜 변경만 기록".
4. 테스트: 수집기 2회 연속 실행 후 `git status` 에 Modified 0 건임을 확인.

---

## 5. 본 문서의 한계

- 이번 git-guard cleanup 세션에서는 **코드 수정 없음**. `.gitignore` 로 `data/raw/kosha/**` 와 `data/normalized/**` 를 빼면 flapping 이 서버 git 에 전파되지 않으므로 단기 해결로는 충분.
- 그러나 수집기가 중복 write 를 계속한다는 사실은 **mtime / disk IO / OneDrive 동기화** 부담으로 남으므로, 본 정책을 후속 PR 에서 반드시 적용.
