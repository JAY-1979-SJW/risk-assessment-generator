# collector 안정화 사전 상태 기록

## git 상태

- **branch**: master
- **HEAD**: 1f2299b6ff3ede865da4de6e7d28ca4c8e100874
- **working tree**: clean (nothing to commit)

## 주요 파일 추적 상태

| 파일 | 상태 |
|------|------|
| `data/risk_db/law_raw/laws_index.json` | git 추적 중 (gitignore 미적용) |
| `data/raw/law_content/` | gitignore 적용 (.gitignore:118) |
| `data/raw/law_api/law/*/laws_index.json` | 예외 패턴으로 추적 중 (.gitignore:97) |

## API 키 상태

| 키 | 상태 |
|----|------|
| DATA_GO_KR_SERVICE_KEY | 없음 (dry-run 모드) |
| LAW_GO_KR_OC | 없음 (dry-run 모드) |

## 검증 전략 결정

- `law_statutes.py run()` 직접 호출 시 `fetched_at` 타임스탬프 갱신으로 tracked 파일(`laws_index.json`) 항상 수정 발생
- API 키 없어 실제 수집 불가 — dry-run 결과는 items=[] (실제 데이터와 다름)
- **채택 전략**: 실제 `laws_index.json` 데이터를 fixture로 사용하는 격리 스텁 실행
  - temp 파일에만 쓰기 → tracked 파일 무변경
  - `fetched_at`를 고정값으로 설정 → save_json 동작 정확 검증
  - git status는 두 차례 실행 전후 모두 clean 유지
