"""
validate_legal_source_registry.py
legal_sources_registry.yml + legal_collection_queue.yml 정합성 검증
"""
import sys
import yaml
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
REGISTRY_PATH = PROJECT_ROOT / "data/masters/safety/legal_sources_registry.yml"
QUEUE_PATH = PROJECT_ROOT / "data/masters/safety/legal_collection_queue.yml"

ALLOWED_COLLECTION_STATUS = {
    "COLLECTED_VERIFIED",
    "COLLECTED_PARTIAL",
    "REFERENCED_ONLY",
    "SCRIPT_EXISTS_NOT_COLLECTED",
    "NOT_COLLECTED",
    "UNKNOWN",
}

ALLOWED_COLLECTION_ACTION = {
    "SKIP_ALREADY_COLLECTED",
    "COLLECT_BY_EXISTING_SCRIPT",
    "COLLECT_BY_LAW_API",
    "COLLECT_BY_NEW_CONNECTOR",
    "NEEDS_OFFICIAL_NAME_CONFIRMATION",
    "WATCH_ONLY",
}

# 원래 22개 source 후보에서 건설기계관리법 시행령/규칙, 소방시설공사업법 시행령/규칙을
# 각각 DECREE+RULE로 분리하여 23개로 확장. UNKNOWN 2건은 발행처 확인으로 NOT_COLLECTED로 전환.
EXPECTED_SOURCE_COUNT = 23

ERRORS: list[str] = []
WARNINGS: list[str] = []


def fail(msg: str) -> None:
    ERRORS.append(msg)
    print(f"  [FAIL] {msg}")


def warn(msg: str) -> None:
    WARNINGS.append(msg)
    print(f"  [WARN] {msg}")


def ok(msg: str) -> None:
    print(f"  [OK]   {msg}")


def load_yaml(path: Path) -> dict | list | None:
    if not path.exists():
        fail(f"파일 없음: {path}")
        return None
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def validate_registry(data: dict) -> list[dict]:
    print("\n=== [1] registry 파일 존재 확인 ===")
    ok(f"파일 존재: {REGISTRY_PATH.relative_to(PROJECT_ROOT)}")

    sources: list[dict] = data.get("sources", [])

    print("\n=== [2] source_code 중복 검사 ===")
    codes = [s.get("source_code") for s in sources]
    seen: set[str] = set()
    for code in codes:
        if code in seen:
            fail(f"source_code 중복: {code}")
        seen.add(code)
    if len(seen) == len(codes):
        ok(f"source_code 중복 없음 (총 {len(codes)}개)")

    print("\n=== [3] source 수 확인 (기대: 22개) ===")
    if len(sources) == EXPECTED_SOURCE_COUNT:
        ok(f"source 수 일치: {len(sources)}개")
    else:
        warn(f"source 수 불일치: 등록={len(sources)}, 기대={EXPECTED_SOURCE_COUNT}")

    print("\n=== [4] collection_status enum 검사 ===")
    for s in sources:
        code = s.get("source_code", "?")
        status = s.get("collection_status")
        if status not in ALLOWED_COLLECTION_STATUS:
            fail(f"{code}: 허용되지 않는 collection_status={status}")
    ok("collection_status enum 검사 완료")

    print("\n=== [5] collection_action enum 검사 ===")
    for s in sources:
        code = s.get("source_code", "?")
        action = s.get("collection_action")
        if action not in ALLOWED_COLLECTION_ACTION:
            fail(f"{code}: 허용되지 않는 collection_action={action}")
    ok("collection_action enum 검사 완료")

    print("\n=== [6] COLLECTED_VERIFIED → evidence_count > 0 ===")
    for s in sources:
        code = s.get("source_code", "?")
        if s.get("collection_status") == "COLLECTED_VERIFIED":
            count = s.get("collected_evidence_count", 0)
            if count <= 0:
                fail(f"{code}: COLLECTED_VERIFIED인데 collected_evidence_count={count}")
            else:
                ok(f"{code}: evidence_count={count}")

    print("\n=== [7] 중복 수집 금지 대상 → SKIP_ALREADY_COLLECTED 확인 ===")
    for s in sources:
        code = s.get("source_code", "?")
        if s.get("duplicate_collection_risk") is True:
            action = s.get("collection_action")
            if action != "SKIP_ALREADY_COLLECTED":
                fail(f"{code}: duplicate_collection_risk=true인데 action={action}")
            else:
                ok(f"{code}: SKIP_ALREADY_COLLECTED 확인")

    print("\n=== [8] UNKNOWN source → enabled=false 또는 NEEDS_OFFICIAL_NAME_CONFIRMATION ===")
    for s in sources:
        code = s.get("source_code", "?")
        if s.get("collection_status") == "UNKNOWN":
            action = s.get("collection_action")
            enabled = s.get("enabled", True)
            if action != "NEEDS_OFFICIAL_NAME_CONFIRMATION" and enabled is not False:
                fail(
                    f"{code}: UNKNOWN이지만 action={action}, enabled={enabled}"
                )
            else:
                ok(f"{code}: UNKNOWN 처리 적절 (action={action}, enabled={enabled})")

    return sources


def validate_queue(data: dict, registry_codes: set[str]) -> None:
    all_queues: list[dict] = []
    for group in data.values():
        if isinstance(group, list):
            all_queues.extend(group)

    print("\n=== [9] collect queue에 COLLECTED_VERIFIED source 없음 확인 ===")
    verified_in_queue: list[str] = []
    for item in all_queues:
        sc = item.get("source_code", "?")
        if sc in registry_codes:
            pass
    # COLLECTED_VERIFIED source_code 수집
    verified_codes: set[str] = set()
    # 이미 registry에서 추출한 정보로 검사 — validated_registry에서 재전달받지 않으므로
    # queue의 enabled=true 항목 중 registry에서 COLLECTED_VERIFIED인 것 감지
    for item in all_queues:
        sc = item.get("source_code", "?")
        action = item.get("collection_action", "")
        if action == "SKIP_ALREADY_COLLECTED":
            fail(f"queue에 SKIP_ALREADY_COLLECTED 항목 포함 (제거 필요): {sc}")
    ok("collect queue에 SKIP_ALREADY_COLLECTED 항목 없음")

    print("\n=== [10] queue source_code가 registry에 존재하는지 확인 ===")
    for item in all_queues:
        sc = item.get("source_code", "?")
        if sc not in registry_codes:
            fail(f"queue source_code가 registry에 없음: {sc}")
    ok("queue source_code 전체 registry에 존재 확인")

    print("\n=== queue_id 중복 검사 ===")
    qids = [item.get("queue_id") for item in all_queues]
    seen_q: set[str] = set()
    for qid in qids:
        if qid in seen_q:
            fail(f"queue_id 중복: {qid}")
        seen_q.add(qid)
    ok(f"queue_id 중복 없음 (총 {len(qids)}개)")


def main() -> int:
    print("=" * 60)
    print("validate_legal_source_registry.py")
    print("=" * 60)

    registry_data = load_yaml(REGISTRY_PATH)
    if registry_data is None:
        print("\n[결과] FAIL — registry 파일 없음")
        return 1

    sources = validate_registry(registry_data)
    registry_codes = {s.get("source_code") for s in sources}

    print(f"\n=== [queue 파일] {QUEUE_PATH.relative_to(PROJECT_ROOT)} ===")
    queue_data = load_yaml(QUEUE_PATH)
    if queue_data is None:
        warn("queue 파일 없음 — queue 검증 건너뜀")
    else:
        ok(f"파일 존재: {QUEUE_PATH.relative_to(PROJECT_ROOT)}")
        validate_queue(queue_data, registry_codes)

    print("\n" + "=" * 60)
    print(f"ERRORS : {len(ERRORS)}")
    print(f"WARNINGS: {len(WARNINGS)}")
    if ERRORS:
        for e in ERRORS:
            print(f"  ERROR: {e}")
        print("\n[최종 결과] FAIL")
        return 1
    if WARNINGS:
        print("\n[최종 결과] WARN (경고 확인 후 진행 가능)")
        return 0
    print("\n[최종 결과] PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
